from django.utils import timezone
from datetime import timedelta
from .models import ActiveUser, ActiveCustomer

def cleanup_inactive_locations(minutes=5):
    """
    Deletes records from ActiveUser and ActiveCustomer tables 
    where updated_at is older than the specified minutes (default: 5 minutes).
    """
    cutoff_time = timezone.now() - timedelta(minutes=minutes)
    deleted_users, _ = ActiveUser.objects.filter(updated_at__lt=cutoff_time).delete()
    deleted_customers, _ = ActiveCustomer.objects.filter(updated_at__lt=cutoff_time).delete()
    return deleted_users, deleted_customers
