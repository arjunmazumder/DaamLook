import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware

User = get_user_model()

@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        headers = dict(scope.get('headers', []))
        if b'authorization' in headers:
            try:
                token_name, token_key = headers[b'authorization'].decode().split()
                if token_name.lower() == 'bearer':
                    decoded_data = jwt.decode(token_key, settings.JWT_SECRET_KEY, algorithms=["HS256"])
                    scope['user'] = await get_user(decoded_data['user_id'])
            except Exception:
                pass
        
        # If token is not in header, check query string (e.g. ws://...?token=abc)
        if 'user' not in scope or scope['user'] is None:
            query_string = scope.get('query_string', b'').decode()
            if 'token=' in query_string:
                try:
                    token_key = query_string.split('token=')[1].split('&')[0]
                    decoded_data = jwt.decode(token_key, settings.JWT_SECRET_KEY, algorithms=["HS256"])
                    scope['user'] = await get_user(decoded_data['user_id'])
                except Exception:
                    pass

        return await super().__call__(scope, receive, send)
