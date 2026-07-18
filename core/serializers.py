from rest_framework import serializers
from .models import ActiveUser, ActiveCustomer

class UpdateLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActiveUser
        fields = ['latitude', 'longitude']

class UpdateCustomerLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActiveCustomer
        fields = ['category', 'latitude', 'longitude']
