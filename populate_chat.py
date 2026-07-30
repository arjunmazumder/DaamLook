import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'damlook.settings')
django.setup()

from users.models import User
from core.models import GlobalChatSession, GlobalChatMessage

def populate():
    buyer_phone = "01958480342"
    provider_phone = "01798916082"
    password = "123456"

    # Get or create Buyer
    buyer, created = User.objects.get_or_create(phone_number=buyer_phone)
    if created:
        buyer.set_password(password)
        buyer.full_name = "Test Buyer"
        buyer.is_active = True
        buyer.is_phone_verified = True
        buyer.save()
        print(f"Created Buyer: {buyer_phone}")
    else:
        print(f"Buyer {buyer_phone} already exists.")

    # Get or create Service Provider
    provider, created = User.objects.get_or_create(phone_number=provider_phone)
    if created:
        provider.set_password(password)
        provider.full_name = "Test Service Provider"
        provider.is_active = True
        provider.is_phone_verified = True
        provider.save()
        print(f"Created Provider: {provider_phone}")
    else:
        print(f"Provider {provider_phone} already exists.")

    # Create SERVICE chat session
    service_session, _ = GlobalChatSession.objects.get_or_create(
        buyer=buyer,
        seller=provider,
        chat_type='SERVICE'
    )
    print("Created SERVICE chat session.")

    # Add messages to SERVICE chat
    if not service_session.messages.exists():
        GlobalChatMessage.objects.create(session=service_session, sender=buyer, message="Hi, I need AC Repair service.", message_type='TEXT')
        GlobalChatMessage.objects.create(session=service_session, sender=provider, message="Hello! Yes, we provide AC repair. What is the issue?", message_type='TEXT')
        GlobalChatMessage.objects.create(session=service_session, sender=buyer, message="It is not cooling.", message_type='TEXT')
        GlobalChatMessage.objects.create(session=service_session, sender=provider, message="Okay, our technician will visit tomorrow.", message_type='TEXT')
        print("Added messages to SERVICE chat.")

    # Create VENDOR chat session
    vendor_session, _ = GlobalChatSession.objects.get_or_create(
        buyer=buyer,
        seller=provider,
        chat_type='VENDOR'
    )
    print("Created VENDOR chat session.")

    # Add messages to VENDOR chat
    if not vendor_session.messages.exists():
        GlobalChatMessage.objects.create(session=vendor_session, sender=buyer, message="Is the Samsung Galaxy S24 Ultra in stock?", message_type='TEXT')
        GlobalChatMessage.objects.create(session=vendor_session, sender=provider, message="Yes, it is available in Titanium Black.", message_type='TEXT')
        GlobalChatMessage.objects.create(session=vendor_session, sender=buyer, message="What is the price?", message_type='TEXT')
        GlobalChatMessage.objects.create(session=vendor_session, sender=provider, message="It is 1,20,000 BDT with official warranty.", message_type='TEXT')
        print("Added messages to VENDOR chat.")

    print("Successfully populated chatting data.")

if __name__ == '__main__':
    populate()
