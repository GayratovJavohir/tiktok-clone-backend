from django.db import models
from users.models import UserModel
from posts.models import Post

class ChatRoom(models.Model):
    DIRECT = "direct"
    GROUP = "group"
    ROOM_TYPES = [(DIRECT, "Direct"), (GROUP, "Group")]
    
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES, default=DIRECT)
    title = models.CharField(max_length=120, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    last_message_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Room({self.id}, {self.room_type})"
    
    
    
class RoomParticipant(models.Model):
    room = models.ForeignKey(ChatRoom, related_name="participants", on_delete=models.CASCADE)
    user = models.ForeignKey(UserModel, related_name="chat_participants", on_delete=models.CASCADE)
    
    last_read_at = models.DateTimeField(blank=True, null=True)
    
    joined_at = models.DateTimeField(auto_now_add=True)
    
    
    class Meta:
        unique_together = ("room", "user")

    def __str__(self):
        return f"{self.user} in room {self.room_id}"



class Message(models.Model):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    GIF = "gif"
    POST = "post"
    FILE = "file"
    REACTION = "reaction"

    TYPES = [
        (TEXT, "Text"),
        (IMAGE, "Image"),
        (VIDEO, "Video"),
        (FILE, "File"),
        (GIF, "Gif"),
        (REACTION, "Reaction"),
        (POST, "Post"),
    ]

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name="sent_messages")

    message_type = models.CharField(max_length=10, choices=TYPES, default=TEXT)
    text = models.TextField(blank=True, null=True)
    media_url = models.URLField(blank=True, null=True)

    shared_post = models.ForeignKey(
        Post,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="shared_in_messages"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Msg({self.id}) in room {self.room_id}"