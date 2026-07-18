import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'damlook.settings')
django.setup()

from users.models import User

for u in User.objects.all():
    u.is_phone_verified = True
    u.is_approved = True
    u.save()

print("Phone numbers verified and users approved.")
