from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Prefetch

from .models import ChatRoom, Message, RoomParticipant
from .serializers import ChatRoomSerializer, MessageSerializer, CreateRoomSerializer
from .services import get_or_create_direct_room, create_group_room
from .pagination import CustomPagination


class ChatRoomViewSet(viewsets.ModelViewSet):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            ChatRoom.objects
            .filter(participants__user=self.request.user)
            .prefetch_related(
                Prefetch(
                    "participants",
                    queryset=RoomParticipant.objects.select_related("user")
                )
            )
            .prefetch_related("messages__sender")
            .order_by("-last_message_at", "-created_at")
            .distinct()
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    @action(detail=False, methods=["post"], url_path="create")
    def create_room(self, request):
        ser = CreateRoomSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        if data["room_type"] == "direct":
            room = get_or_create_direct_room(request.user, data["participant_ids"][0])
        else:
            room = create_group_room(
                request.user,
                data["participant_ids"],
                title=data.get("title") or ""
            )

        return Response(
            ChatRoomSerializer(room, context=self.get_serializer_context()).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"], url_path="read")
    def mark_read(self, request, pk=None):
        room = self.get_object()
        rp = RoomParticipant.objects.filter(room=room, user=request.user).first()
        if not rp:
            return Response({"detail": "Not a participant"}, status=403)

        rp.last_read_at = timezone.now()
        rp.save(update_fields=["last_read_at"])
        return Response({"ok": True})


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        room_id = self.request.query_params.get("room")
        qs = Message.objects.select_related(
            "sender",
            "room",
            "shared_post",
            "shared_post__author",
        ).order_by("-created_at")

        if room_id:
            qs = qs.filter(room_id=room_id)

        return qs.filter(room__participants__user=self.request.user).distinct()

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    def perform_create(self, serializer):
        room = serializer.validated_data["room"]
        if not RoomParticipant.objects.filter(room=room, user=self.request.user).exists():
            raise permissions.PermissionDenied("Not a participant of this room.")

        msg = serializer.save(sender=self.request.user)
        ChatRoom.objects.filter(id=room.id).update(last_message_at=msg.created_at)
        
    

    @action(detail=False, methods=["get"], url_path="room/(?P<room_id>[^/.]+)/history")
    def history(self, request, room_id=None):
        qs = self.get_queryset().filter(room_id=room_id)
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = MessageSerializer(page, many=True, context=self.get_serializer_context())
            return self.get_paginated_response(ser.data)
        return Response(MessageSerializer(qs, many=True, context=self.get_serializer_context()).data)