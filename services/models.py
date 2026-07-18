from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    icon_img = models.ImageField(upload_to='services/categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ServiceProviderBusinessProfile(models.Model):
    provider = models.OneToOneField(User, on_delete=models.CASCADE, related_name='business_profile')
    shop_name = models.CharField(max_length=255)
    contact_number = models.CharField(max_length=20)
    address = models.TextField(blank=True, null=True)
    categories = models.ManyToManyField(ServiceCategory, related_name='providers')
    average_rating = models.FloatField(default=0.0)
    total_reviews = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.shop_name

class ServiceBooking(models.Model):
    STATUS_CHOICES = (
        ('INQUIRY', 'Inquiry'),
        ('PENDING_RESPONSE', 'Pending Response'),
        ('COMING', 'Coming'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_bookings')
    provider = models.ForeignKey(ServiceProviderBusinessProfile, on_delete=models.CASCADE, related_name='received_bookings')
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True, related_name='bookings')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='INQUIRY')
    scheduled_date = models.DateField(blank=True, null=True)
    scheduled_time = models.TimeField(blank=True, null=True)
    problem_description = models.TextField(blank=True, null=True)
    attachment = models.ImageField(upload_to='services/bookings/', blank=True, null=True)
    buyer_latitude = models.FloatField(blank=True, null=True)
    buyer_longitude = models.FloatField(blank=True, null=True)
    cancellation_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking #{self.id} - {self.buyer.phone_number} to {self.provider.shop_name}"

class ChatMessage(models.Model):
    booking = models.ForeignKey(ServiceBooking, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message = models.TextField()
    attachment = models.FileField(upload_to='services/chats/', blank=True, null=True)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message {self.id} on Booking {self.booking_id}"

class ProviderNotification(models.Model):
    provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    booking = models.ForeignKey(ServiceBooking, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.provider.phone_number}"

class ProviderReview(models.Model):
    booking = models.OneToOneField(ServiceBooking, on_delete=models.CASCADE, related_name='review')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reviews')
    reviewee = models.ForeignKey(ServiceProviderBusinessProfile, on_delete=models.CASCADE, related_name='received_reviews')
    rating_stars = models.IntegerField(default=5)
    price_fairness = models.IntegerField(default=5)
    behavior_rating = models.IntegerField(default=5)
    response_time_rating = models.IntegerField(default=5)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.reviewee.shop_name} by {self.reviewer.phone_number}"

