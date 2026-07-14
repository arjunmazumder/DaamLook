from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from .models import User, UserSession
from .utils import generate_access_token, generate_refresh_token, hash_token

def login_user(user):
    access_token = generate_access_token(user)
    refresh_token = generate_refresh_token()
    hashed_refresh_token = hash_token(refresh_token)

    expires_at = timezone.now() + timedelta(days=settings.JWT_REFRESH_EXPIRATION_DAYS)

    UserSession.objects.create(
        user=user,
        refresh_token=hashed_refresh_token,
        expires_at=expires_at
    )

    return access_token, refresh_token

def refresh_tokens(refresh_token):
    if not refresh_token:
        return None, None

    hashed_token = hash_token(refresh_token)
    
    try:
        session = UserSession.objects.get(refresh_token=hashed_token)
    except UserSession.DoesNotExist:
        return None, None
        
    if session.is_expired():
        session.delete()
        return None, None

    new_access_token = generate_access_token(session.user)
    new_refresh_token = generate_refresh_token()
    new_hashed_refresh_token = hash_token(new_refresh_token)
    
    session.refresh_token = new_hashed_refresh_token
    session.expires_at = timezone.now() + timedelta(days=settings.JWT_REFRESH_EXPIRATION_DAYS)
    session.save()

    return new_access_token, new_refresh_token

def logout_user(refresh_token):
    if not refresh_token:
        return
    hashed_token = hash_token(refresh_token)
    UserSession.objects.filter(refresh_token=hashed_token).delete()
