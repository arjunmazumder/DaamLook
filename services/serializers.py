from rest_framework import serializers
from .models import ServiceCategory

class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ['id', 'name', 'description', 'icon_img', 'is_active', 'created_at', 'updated_at']

from .models import ServiceProviderBusinessProfile

class ServiceProviderBusinessProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceProviderBusinessProfile
        fields = ['id', 'provider', 'shop_name', 'contact_number', 'address', 'categories', 'average_rating', 'total_reviews', 'created_at', 'updated_at']
        read_only_fields = ['average_rating', 'total_reviews']

class NearbyProviderSerializer(serializers.Serializer):
    provider_id = serializers.IntegerField()
    shop_name = serializers.CharField()
    contact_number = serializers.CharField(allow_blank=True, required=False)
    address = serializers.CharField(allow_blank=True, required=False)
    average_rating = serializers.FloatField()
    total_reviews = serializers.IntegerField()
    distance_km = serializers.FloatField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
