from django.contrib.auth import get_user_model
from django.db import transaction
from .models import ChatRoom, RoomParticipant

User = get_user_model()


def get_or_create_direct_room(user, other_user_id: int) -> ChatRoom:
    qs = ChatRoom.objects.filter(room_type=ChatRoom.DIRECT).distinct()
    qs = qs.filter(participants__user=user).filter(participants__user_id=other_user_id)

    room = qs.first()
    if room:
        return room

    with transaction.atomic():
        room = ChatRoom.objects.create(room_type=ChatRoom.DIRECT)
        RoomParticipant.objects.create(room=room, user=user)
        RoomParticipant.objects.create(room=room, user_id=other_user_id)
    return room


def create_group_room(owner, participant_ids, title="") -> ChatRoom:
    unique_ids = set(participant_ids)
    unique_ids.add(owner.id)

    with transaction.atomic():
        room = ChatRoom.objects.create(room_type=ChatRoom.GROUP, title=title or "Group")
        RoomParticipant.objects.bulk_create(
            [RoomParticipant(room=room, user_id=uid) for uid in unique_ids]
        )
    return room