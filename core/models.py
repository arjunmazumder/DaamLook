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
