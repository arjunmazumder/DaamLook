import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'damlook.settings')
django.setup()

from users.models import User
from lookup.models import Lookup
from services.models import ServiceCategory, ServiceProviderBusinessProfile
from core.models import ActiveUser, ActiveCustomer

def run():
    # 1. Create Roles
    buyer_role, _ = Lookup.objects.get_or_create(name='ROLE', value='BUYER')
    provider_role, _ = Lookup.objects.get_or_create(name='ROLE', value='SERVICE_PROVIDER')

    # 2. Create Category
    plumbing, _ = ServiceCategory.objects.get_or_create(name='Plumbing')

    # 3. Create Users
    buyer_user, _ = User.objects.get_or_create(phone_number='01700000001', defaults={'role': buyer_role})
    if not buyer_user.role:
        buyer_user.role = buyer_role
        buyer_user.save()
        
    provider1_user, _ = User.objects.get_or_create(phone_number='01700000002', defaults={'role': provider_role})
    if not provider1_user.role:
        provider1_user.role = provider_role
        provider1_user.save()

    provider2_user, _ = User.objects.get_or_create(phone_number='01700000003', defaults={'role': provider_role})
    if not provider2_user.role:
        provider2_user.role = provider_role
        provider2_user.save()

    # 4. Create Business Profiles
    p1_profile, _ = ServiceProviderBusinessProfile.objects.get_or_create(
        provider=provider1_user, 
        defaults={'shop_name': 'A1 Plumbers', 'contact_number': '01700000002'}
    )
    p1_profile.categories.add(plumbing)

    p2_profile, _ = ServiceProviderBusinessProfile.objects.get_or_create(
        provider=provider2_user, 
        defaults={'shop_name': 'Faraway Plumbers', 'contact_number': '01700000003'}
    )
    p2_profile.categories.add(plumbing)

    # 5. Create ActiveCustomer (Buyer)
    ActiveCustomer.objects.update_or_create(
        user=buyer_user,
        defaults={
            'category': plumbing,
            'latitude': 23.8103,
            'longitude': 90.4125
        }
    )

    # 6. Create ActiveUser (Providers)
    # Provider 1 is nearby (~300 meters away)
    p1_active, _ = ActiveUser.objects.update_or_create(
        user=provider1_user,
        defaults={
            'latitude': 23.8123,  
            'longitude': 90.4145  
        }
    )
    # Ensure it's active right now
    ActiveUser.objects.filter(pk=p1_active.pk).update(updated_at=timezone.now())

    # Provider 2 is far away (~15km away)
    p2_active, _ = ActiveUser.objects.update_or_create(
        user=provider2_user,
        defaults={
            'latitude': 23.7103,  
            'longitude': 90.3125  
        }
    )
    # Ensure it's active right now
    ActiveUser.objects.filter(pk=p2_active.pk).update(updated_at=timezone.now())
    
    print("Test data created successfully!")

if __name__ == '__main__':
    run()
