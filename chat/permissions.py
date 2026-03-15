from rest_framework.permissions import BasePermission
from .models import ChatRoom, RoomParticipant


class IsRoomParticipant(BasePermission):
    message = "You are not a participant of this room."

    def has_object_permission(self, request, obj):
        room = obj if isinstance(obj, ChatRoom) else getattr(obj, "room", None)
        if room is None:
            return False
        return RoomParticipant.objects.filter(room=room, user=request.user).exists()