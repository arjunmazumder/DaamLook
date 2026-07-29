from rest_framework import serializers
from .models import ActiveUser, ActiveCustomer, Commission

class UpdateLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActiveUser
        fields = ['latitude', 'longitude']

class UpdateCustomerLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActiveCustomer
        fields = ['category', 'latitude', 'longitude']

class CommissionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    servicecategory_name = serializers.CharField(source='servicecategory.name', read_only=True)
    
    class Meta:
        model = Commission
        fields = '__all__'

class UnifiedChatStartSerializer(serializers.Serializer):
    provider_id = serializers.IntegerField(required=False, help_text="ID of the Service Provider")
    shop_id = serializers.IntegerField(required=False, help_text="ID of the Vendor/Shop")
