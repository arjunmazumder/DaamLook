from django.db import models

from django.contrib.auth import get_user_model

User = get_user_model()

class ActiveUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='active_location')
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Location for {self.user.phone_number}"

class ActiveCustomer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='active_customer_location')
    category = models.ForeignKey('services.ServiceCategory', on_delete=models.SET_NULL, null=True, blank=True, related_name='active_customers')
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Customer Location for {self.user.phone_number}"

class BroadcastAnnouncement(models.Model):
    TARGET_CHOICES = (
        ('ALL', 'All Users'),
        ('BUYERS', 'Only Buyers'),
        ('VENDORS', 'Only Vendors'),
        ('SERVICE_PROVIDERS', 'Only Service Providers'),
        ('STAFF', 'Only Staff'),
        ('SPECIFIC_USERS', 'Specific Users'),
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    target_audience = models.CharField(max_length=20, choices=TARGET_CHOICES, default='ALL')
    specific_targets = models.ManyToManyField(User, blank=True, related_name='targeted_announcements')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.target_audience})"

class Commission(models.Model):
    category = models.ForeignKey('products.Category', on_delete=models.CASCADE, null=True, blank=True, related_name='commissions')
    servicecategory = models.ForeignKey('services.ServiceCategory', on_delete=models.CASCADE, null=True, blank=True, related_name='commissions')
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Commission in percentage (%)")
    flat = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Flat commission amount")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.category:
            return f"Commission for Product Category: {self.category.name}"
        if self.servicecategory:
            return f"Commission for Service Category: {self.servicecategory.name}"
        return "Global Commission"


class GlobalChatSession(models.Model):
    CHAT_TYPE_CHOICES = (
        ('VENDOR', 'Vendor Chat'),
        ('SERVICE', 'Service Provider Chat'),
    )
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='global_chats_as_buyer')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='global_chats_as_seller')
    chat_type = models.CharField(max_length=20, choices=CHAT_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('buyer', 'seller', 'chat_type')

    def __str__(self):
        return f"{self.chat_type} Chat: {self.buyer.phone_number} & {self.seller.phone_number}"

class GlobalChatMessage(models.Model):
    MESSAGE_TYPE_CHOICES = (
        ('TEXT', 'Text'),
        ('IMAGE', 'Image'),
        ('SYSTEM_ALERT', 'System Alert'),
        ('INVOICE', 'Invoice'),
    )
    session = models.ForeignKey(GlobalChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_global_messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='TEXT')
    message = models.TextField(blank=True, null=True)
    attachment = models.FileField(upload_to='chats/', blank=True, null=True)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Message {self.id} in Session {self.session_id}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Touch the session to update its updated_at field for Inbox sorting
        self.session.save(update_fields=['updated_at'])

class Policy(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Policies"

    def __str__(self):
        return self.title

class AboutUs(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "About Us"

    def __str__(self):
        return self.title
