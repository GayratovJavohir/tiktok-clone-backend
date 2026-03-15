import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils import timezone

from .models import ChatRoom, RoomParticipant, Message


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = int(self.scope["url_route"]["kwargs"]["room_id"])
        self.room_group_name = f"chat_{self.room_id}"

        user = self.scope["user"]
        if user.is_anonymous:
            await self.close(code=4001)
            return

        is_participant = await self.is_participant(user.id, self.room_id)
        if not is_participant:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """
        Client yuboradigan payload misollar:
        1) message:
           {"type":"message","text":"salom","message_type":"text"}
        2) typing:
           {"type":"typing","is_typing":true}
        3) read:
           {"type":"read"}
        """
        data = json.loads(text_data)
        event_type = data.get("type")

        if event_type == "message":
            await self.handle_message(data)
        elif event_type == "typing":
            await self.handle_typing(data)
        elif event_type == "read":
            await self.handle_read()
        else:
            await self.send(text_data=json.dumps({"error": "Unknown event type"}))

    async def handle_message(self, data):
        user = self.scope["user"]
        text = data.get("text")
        message_type = data.get("message_type", "text")
        media_url = data.get("media_url")

        msg = await self.create_message(
            room_id=self.room_id,
            sender_id=user.id,
            text=text,
            message_type=message_type,
            media_url=media_url,
        )

        # roomdagi hammaga tarqatamiz
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.message",
                "message": {
                    "id": msg["id"],
                    "room": self.room_id,
                    "sender": msg["sender"],
                    "message_type": msg["message_type"],
                    "text": msg["text"],
                    "media_url": msg["media_url"],
                    "created_at": msg["created_at"],
                },
            },
        )

    async def handle_typing(self, data):
        user = self.scope["user"]
        is_typing = bool(data.get("is_typing", False))

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.typing",
                "payload": {"user_id": user.id, "username": user.username, "is_typing": is_typing},
            },
        )

    async def handle_read(self):
        user = self.scope["user"]
        await self.mark_read(user.id, self.room_id)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.read",
                "payload": {"user_id": user.id, "username": user.username, "read_at": timezone.now().isoformat()},
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({"type": "message", **event}))

    async def chat_typing(self, event):
        await self.send(text_data=json.dumps({"type": "typing", **event}))

    async def chat_read(self, event):
        await self.send(text_data=json.dumps({"type": "read", **event}))

    # Channels naming: "chat.message" -> chat_message method
    chat_message = chat_message
    chat_typing = chat_typing
    chat_read = chat_read

    # ---------- DB ops ----------
    @sync_to_async
    def is_participant(self, user_id, room_id) -> bool:
        return RoomParticipant.objects.filter(room_id=room_id, user_id=user_id).exists()

    @sync_to_async
    def create_message(self, room_id, sender_id, text, message_type, media_url):
        msg = Message.objects.create(
            room_id=room_id,
            sender_id=sender_id,
            text=text,
            message_type=message_type,
            media_url=media_url,
        )
        ChatRoom.objects.filter(id=room_id).update(last_message_at=msg.created_at)

        # response uchun minimal data
        return {
            "id": msg.id,
            "sender": {"id": msg.sender_id, "username": msg.sender.username},
            "message_type": msg.message_type,
            "text": msg.text,
            "media_url": msg.media_url,
            "created_at": msg.created_at.isoformat(),
        }

    @sync_to_async
    def mark_read(self, user_id, room_id):
        RoomParticipant.objects.filter(room_id=room_id, user_id=user_id).update(last_read_at=timezone.now())