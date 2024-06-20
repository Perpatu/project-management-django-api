import urllib.parse

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token


@database_sync_to_async
def get_user(token):
    """returns user from database"""
    try:
        user = Token.objects.get(key=token)
        return user.user
    except Token.DoesNotExist:
        return AnonymousUser()


def get_token(headers):
    """search token for user in headers"""
    token = None
    for tup in headers:
        if tup[0] == b'cookie':
            encoded_cookie = tup[1]
            decoded_cookie = urllib.parse.unquote(encoded_cookie)
            decoded_parts = decoded_cookie.split(';')
            for auth in decoded_parts:
                if auth.startswith(' auth=') or auth.startswith('auth='):
                    token = auth.split('=')[1]
                    break

        # if tup[0] == b'authorization':
        #    """for postman remember to delete"""
        #    encoded_cookie = tup[1]
        #    decoded_cookie = urllib.parse.unquote(encoded_cookie)
        #    token = decoded_cookie.split(' ')[1]
    return token


class AuthChannelsMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        """if user is authenticated create scope['user'] = user otherwise
        scope['user'] = AnonymousUser and return 0"""

        headers = scope['headers']
        token = get_token(headers)
        user = await get_user(token)
        if user == AnonymousUser():
            scope['user'] = AnonymousUser()
            return 0
        scope['user'] = user
        return await self.app(scope, receive, send)


def auth_channels(app):
    return AuthChannelsMiddleware(app)
