import os
import django
import random
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'damlook.settings')
django.setup()

from users.models import User
from lookup.models import Lookup
from services.models import (
    ServiceCategory, ServiceProviderBusinessProfile, Recentwork,
    ServiceBooking, ServiceInvoice, ServiceProviderReview, ServiceCommission
)
from core.models import Commission

def run():
    print("Seeding extra services data...")

    try:
        buyer = User.objects.get(phone_number='01700000001')
        p1 = User.objects.get(phone_number='01700000002')
        p2 = User.objects.get(phone_number='01700000003')
        category = ServiceCategory.objects.get(name='Plumbing')
        p1_profile = ServiceProviderBusinessProfile.objects.get(provider=p1)
        p2_profile = ServiceProviderBusinessProfile.objects.get(provider=p2)
    except Exception as e:
        print("Required base data not found. Please run seed_data.py first!")
        return

    # 1. Create Recentwork
    print("Creating Recent Works...")
    Recentwork.objects.get_or_create(
        provider=p1_profile,
        title="Fixed leaking pipe in Dhanmondi",
        description="Repaired a major leak in the main water supply line."
    )
    Recentwork.objects.get_or_create(
        provider=p2_profile,
        title="Installed new bathroom fittings",
        description="Complete installation of modern bathroom fittings for a new apartment."
    )

    # 2. Set global commission rule (if not exists)
    print("Setting up Commission Rule...")
    Commission.objects.get_or_create(
        category=None,
        servicecategory=None,
        defaults={'percentage': 10.00}  # 10% global commission
    )

    # 3. Create Bookings
    print("Creating Bookings...")
    # PENDING booking
    ServiceBooking.objects.get_or_create(
        buyer=buyer,
        provider=p1_profile,
        category=category,
        status='PENDING',
        defaults={
            'service_description': 'Need help fixing a broken tap.',
            'scheduled_date': timezone.now().date() + timedelta(days=1),
            'scheduled_time': (timezone.now() + timedelta(hours=2)).time(),
        }
    )

    # CONFIRMED booking
    ServiceBooking.objects.get_or_create(
        buyer=buyer,
        provider=p2_profile,
        category=category,
        status='CONFIRMED',
        defaults={
            'service_description': 'Water heater installation.',
            'scheduled_date': timezone.now().date() + timedelta(days=2),
        }
    )

    # COMPLETED booking (requires invoice and review)
    completed_booking, created = ServiceBooking.objects.get_or_create(
        buyer=buyer,
        provider=p1_profile,
        category=category,
        status='COMPLETED',
        payment_status='PAID',
        defaults={
            'service_description': 'Kitchen sink unblocking.',
            'service_bill': Decimal('1500.00'),
        }
    )

    if created:
        print("Creating Invoice and Review for completed booking...")
        # Create Invoice
        ServiceInvoice.objects.create(
            booking=completed_booking,
            base_amount=Decimal('1500.00'),
            payment_status='PAID',
            payment_method='CASH'
        )
        # Create Review
        ServiceProviderReview.objects.create(
            booking=completed_booking,
            reviewer=buyer,
            reviewee=p1_profile,
            bill_rating=5,
            on_time_delivery_rating=4,
            response_and_behavior_rating=5,
            honesty_rating=5,
            comment="Great service! Fixed the issue very quickly."
        )

    print("Extra Services data seeded successfully!")

if __name__ == '__main__':
    run()
