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

from .models import GlobalChatSession, GlobalChatMessage
from django.contrib.auth import get_user_model

User = get_user_model()

class GlobalChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = GlobalChatMessage
        fields = '__all__'
        read_only_fields = ['sender', 'timestamp', 'is_read']

    def get_sender_name(self, obj):
        return getattr(obj.sender, 'phone_number', getattr(obj.sender, 'username', getattr(obj.sender, 'email', str(obj.sender.id))))

class GlobalChatSessionSerializer(serializers.ModelSerializer):
    latest_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    seller_name = serializers.CharField(source='seller.phone_number', read_only=True)
    buyer_name = serializers.CharField(source='buyer.phone_number', read_only=True)

    class Meta:
        model = GlobalChatSession
        fields = '__all__'
        read_only_fields = ['buyer', 'created_at', 'updated_at']

    def get_latest_message(self, obj):
        message = obj.messages.first()
        if message:
            return GlobalChatMessageSerializer(message).data
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0
