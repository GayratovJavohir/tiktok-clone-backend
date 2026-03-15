from rest_framework import serializers
from .models import ChatRoom, RoomParticipant, Message
from users.models import UserModel
from posts.models import Post


class UserMiniSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = UserModel
        fields = ("id", "username", "first_name", "last_name", "avatar")

    def get_avatar(self, obj):
        avatar = getattr(obj, "avatar", None)
        if not avatar:
            return None

        try:
            url = avatar.url
        except Exception:
            return None

        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(url)
        return url
    
class SharedPostMiniSerializer(serializers.ModelSerializer):
    author = UserMiniSerializer(read_only=True)
    image = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ("id", "title", "caption", "image", "video", "author")

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url

    def get_video(self, obj):
        if not obj.video:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.video.url)
        return obj.video.url


class MessageSerializer(serializers.ModelSerializer):
    sender = UserMiniSerializer(read_only=True)
    shared_post = SharedPostMiniSerializer(read_only=True)
    shared_post_id = serializers.PrimaryKeyRelatedField(
        queryset=Post.objects.all(),
        source="shared_post",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Message
        fields = (
            "id",
            "room",
            "sender",
            "message_type",
            "text",
            "media_url",
            "shared_post",
            "shared_post_id",
            "created_at",
        )
        read_only_fields = ("sender", "created_at")
        



class RoomParticipantSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model = RoomParticipant
        fields = ("user", "last_read_at", "joined_at")


class ChatRoomSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = (
            "id",
            "room_type",
            "title",
            "name",
            "username",
            "avatar",
            "last_message_at",
            "last_message",
            "unread_count",
            "created_at",
        )

    def get_other_user(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None

        participant = obj.participants.exclude(user=request.user).select_related("user").first()
        return participant.user if participant else None

    def get_name(self, obj):
        if obj.room_type == ChatRoom.GROUP:
            return obj.title or "Group"

        other_user = self.get_other_user(obj)
        if not other_user:
            return "Unknown User"

        full_name = f"{other_user.first_name} {other_user.last_name}".strip()
        return full_name or other_user.username

    def get_username(self, obj):
        if obj.room_type == ChatRoom.GROUP:
            return "@group"

        other_user = self.get_other_user(obj)
        return f"@{other_user.username}" if other_user else "@unknown"

    def get_avatar(self, obj):
        if obj.room_type == ChatRoom.GROUP:
            return None

        other_user = self.get_other_user(obj)
        if not other_user:
            return None

        avatar = getattr(other_user, "avatar", None)
        if not avatar:
            return None

        try:
            url = avatar.url
        except Exception:
            return None

        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(url)
        return url

    def get_last_message(self, obj):
        msg = obj.messages.select_related("sender").order_by("-created_at").first()
        if not msg:
            return None
        return MessageSerializer(msg, context=self.context).data

    def get_unread_count(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return 0

        rp = obj.participants.filter(user=request.user).first()
        if not rp:
            return 0

        qs = obj.messages.exclude(sender=request.user)

        if not rp.last_read_at:
            return qs.count()

        return qs.filter(created_at__gt=rp.last_read_at).count()


class CreateRoomSerializer(serializers.Serializer):
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    room_type = serializers.ChoiceField(choices=["direct", "group"], default="direct")
    title = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        request = self.context.get("request")
        current_user = request.user if request else None

        if attrs["room_type"] == "direct" and len(attrs["participant_ids"]) != 1:
            raise serializers.ValidationError("Direct room needs exactly 1 participant_id.")

        if current_user:
            if current_user.id in attrs["participant_ids"]:
                raise serializers.ValidationError("You cannot create a chat with yourself.")

        return attrs