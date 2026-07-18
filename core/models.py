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
