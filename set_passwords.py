import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'damlook.settings')
django.setup()

from users.models import User

for u in User.objects.all():
    u.set_password('123456')
    u.save()

print("Passwords set to '123456' for all users.")
