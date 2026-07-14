import jwt
from django.conf import settings
from rest_framework import authentication
from rest_framework import exceptions
from .models import User

class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        token = None
        
        if auth_header:
            try:
                prefix, token = auth_header.split(' ')
                if prefix.lower() != 'bearer':
                    token = None
            except ValueError:
                token = None
        
        # Fallback to cookie if not in header
        if not token:
            token = request.COOKIES.get('access_token')
            
        if not token:
            return None
            
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Access token expired')
        except jwt.DecodeError:
            raise exceptions.AuthenticationFailed('Invalid token')
            
        user_id = payload.get('user_id')
        if not user_id:
            raise exceptions.AuthenticationFailed('User identifier not found in JWT')
            
        # Stateless authentication: Return an in-memory user instance
        # to avoid database lookups for every protected request.
        user = User(id=user_id, phone_number=payload.get('phone_number'))
        
        return (user, token)
