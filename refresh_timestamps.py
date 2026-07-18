import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'damlook.settings')
django.setup()

from core.models import ActiveUser

# Update all active users to have the current timestamp
ActiveUser.objects.all().update(updated_at=timezone.now())

print("Timestamps refreshed!")
