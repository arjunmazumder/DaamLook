from rest_framework import serializers
from .models import BroadcastAnnouncement, GlobalChatSession, GlobalChatMessage
from users.serializers import UserSerializer
from vendors.serializers import ShopProfileSerializer
from services.serializers import ServiceProviderBusinessProfileSerializer
from .serializers import GlobalChatMessageSerializer

class BroadcastAnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = BroadcastAnnouncement
        fields = '__all__'
        read_only_fields = ['created_at']

class AdminGlobalChatSessionSerializer(serializers.ModelSerializer):
    latest_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    buyer_details = UserSerializer(source='buyer', read_only=True)
    seller_details = serializers.SerializerMethodField()

    class Meta:
        model = GlobalChatSession
        fields = '__all__'

    def get_latest_message(self, obj):
        message = obj.messages.first()
        if message:
            return GlobalChatMessageSerializer(message, context=self.context).data
        return None
    
    def get_unread_count(self, obj):
        return obj.messages.filter(is_read=False).count()

    def get_seller_details(self, obj):
        if obj.chat_type == 'VENDOR' and hasattr(obj.seller, 'vendor_shop_profile'):
            return ShopProfileSerializer(obj.seller.vendor_shop_profile, context=self.context).data
        elif obj.chat_type == 'SERVICE' and hasattr(obj.seller, 'business_profile'):
            return ServiceProviderBusinessProfileSerializer(obj.seller.business_profile, context=self.context).data
        return UserSerializer(obj.seller, context=self.context).data

class AdminGlobalChatSessionDetailSerializer(AdminGlobalChatSessionSerializer):
    all_messages = serializers.SerializerMethodField()

    class Meta(AdminGlobalChatSessionSerializer.Meta):
        pass

    def get_all_messages(self, obj):
        messages = obj.messages.all().order_by('timestamp')
        return GlobalChatMessageSerializer(messages, many=True, context=self.context).data
