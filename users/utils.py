import jwt
import hashlib
import secrets
import random
from datetime import timedelta
from django.utils import timezone
from django.conf import settings

def generate_otp():
    return str(random.randint(100000, 999999))

import requests

def send_otp_sms(phone_number, otp_code):
    if not settings.GREENWEB_SMS_TOKEN or settings.GREENWEB_SMS_TOKEN == 'your_token_here':
        # Mock sending SMS. In production, provide a valid GREENWEB_SMS_TOKEN
        print(f"\n--- SIMULATED SMS ---")
        print(f"To: {phone_number}")
        print(f"Message: Your Daamlook OTP is {otp_code}")
        print(f"---------------------\n")
        return True

    url = "http://api.greenweb.com.bd/api.php"
    
    # BTRC Rule: OTP SMS must start with bracketed company name [Company Name]
    sms_text = f"[Daamlook] Your OTP code is {otp_code}"
    
    data = {
        "token": settings.GREENWEB_SMS_TOKEN,
        "to": phone_number,
        "message": sms_text
    }
    
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        print(f"SMS Sent successfully to {phone_number}: {response.text}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to send SMS to {phone_number}: {e}")
        return False

def generate_access_token(user):
    payload = {
        'user_id': user.id,
        'phone_number': user.phone_number,
        'exp': timezone.now() + timedelta(minutes=settings.JWT_ACCESS_EXPIRATION_MINUTES),
        'iat': timezone.now(),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm='HS256')

def generate_refresh_token():
    return secrets.token_urlsafe(64)

def hash_token(token):
    return hashlib.sha256(token.encode('utf-8')).hexdigest()
