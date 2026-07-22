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

from .models import ChatSession, ChatMessage, ServiceBooking

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'session', 'sender', 'message_type', 'message', 'attachment', 'is_read', 'timestamp']
        read_only_fields = ['id', 'timestamp']

class ChatSessionSerializer(serializers.ModelSerializer):
    latest_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    provider_shop_name = serializers.CharField(source='provider.shop_name', read_only=True)
    buyer_name = serializers.CharField(source='buyer.first_name', read_only=True) # Assuming user has first_name

    class Meta:
        model = ChatSession
        fields = ['id', 'buyer', 'buyer_name', 'provider', 'provider_shop_name', 'is_active', 'created_at', 'updated_at', 'latest_message', 'unread_count']

    def get_latest_message(self, obj):
        message = obj.messages.first()
        if message:
            return ChatMessageSerializer(message).data
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0

class ServiceBookingSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source='buyer.full_name', read_only=True)
    provider_name = serializers.CharField(source='provider.shop_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = ServiceBooking
        fields = '__all__'

from .models import ServiceProviderReview

class ServiceProviderReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceProviderReview
        fields = '__all__'
        read_only_fields = ['reviewer', 'reviewee', 'rating_stars']

from .models import ServiceInvoice

class ServiceInvoiceSerializer(serializers.ModelSerializer):
    buyer_phone = serializers.CharField(source='booking.buyer.phone_number', read_only=True)
    buyer_name = serializers.CharField(source='booking.buyer.full_name', read_only=True)
    provider_shop_name = serializers.CharField(source='booking.provider.shop_name', read_only=True)
    booking_status = serializers.CharField(source='booking.status', read_only=True)

    class Meta:
        model = ServiceInvoice
        fields = '__all__'
        read_only_fields = ['invoice_number', 'total_amount', 'paid_at', 'created_at']
