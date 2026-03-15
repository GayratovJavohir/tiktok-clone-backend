from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser

User = get_user_model()

from channels.auth import AuthMiddlewareStack

def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(AuthMiddlewareStack(inner))

@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope["query_string"].decode()
        query_params = parse_qs(query_string)
        token = query_params.get("token", [None])[0]

        scope["user"] = AnonymousUser()

        if token:
            try:
                validated_token = UntypedToken(token)
                user_id = validated_token["user_id"]
                scope["user"] = await get_user(user_id)
            except (InvalidToken, TokenError, KeyError):
                scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)