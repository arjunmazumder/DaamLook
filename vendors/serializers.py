from rest_framework import serializers
from .models import ShopProfile, ShopReview, VendorChatSession, VendorChatMessage, City

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = '__all__'

class ShopProfileSerializer(serializers.ModelSerializer):
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = ShopProfile
        fields = '__all__'
        read_only_fields = ['user', 'average_rating', 'total_reviews', 'created_at', 'updated_at']

class ShopReviewSerializer(serializers.ModelSerializer):
    reviewer_phone = serializers.CharField(source='reviewer.phone_number', read_only=True)
    reviewer_name = serializers.CharField(source='reviewer.full_name', read_only=True)
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = ShopReview
        fields = '__all__'
        read_only_fields = ['reviewer', 'created_at']

    def validate(self, attrs):
        request = self.context.get('request')
        shop = attrs.get('shop')

        if request and request.user:
            # Check if user is trying to review their own shop
            if shop and shop.user == request.user:
                raise serializers.ValidationError({"error": "You cannot review your own shop."})
                
        return attrs

class VendorChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = VendorChatMessage
        fields = '__all__'
        read_only_fields = ['sender', 'timestamp', 'is_read']

    def get_sender_name(self, obj):
        return getattr(obj.sender, 'phone_number', getattr(obj.sender, 'username', getattr(obj.sender, 'email', str(obj.sender.id))))


class VendorChatSessionSerializer(serializers.ModelSerializer):
    buyer_identifier = serializers.SerializerMethodField()
    shop_name = serializers.CharField(source='vendor.shop_name', read_only=True)
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = VendorChatSession
        fields = '__all__'
        read_only_fields = ['buyer', 'vendor', 'created_at', 'updated_at']

    def get_buyer_identifier(self, obj):
        return getattr(obj.buyer, 'phone_number', getattr(obj.buyer, 'username', getattr(obj.buyer, 'email', str(obj.buyer.id))))

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-timestamp').first()
        if last_msg:
            return VendorChatMessageSerializer(last_msg).data
        return None
