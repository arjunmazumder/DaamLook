from rest_framework import serializers
from .models import ActiveUser, ActiveCustomer, Commission, Policy

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

from orders.models import ChatSessionInvoice, ChatSessionInvoiceCommission
from users.serializers import UserSerializer
from products.serializers import CategorySerializer
from vendors.serializers import ShopProfileSerializer
from services.serializers import ServiceProviderBusinessProfileSerializer

class ChatSessionInvoiceCommissionSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    vendor_phone = serializers.CharField(source='invoice.session.seller.phone_number', read_only=True)
    invoice_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ChatSessionInvoiceCommission
        fields = '__all__'

    def get_invoice_details(self, obj):
        return ChatSessionInvoiceSerializer(obj.invoice, context=self.context).data

class ChatSessionInvoiceSerializer(serializers.ModelSerializer):
    buyer_details = serializers.SerializerMethodField(read_only=True)
    seller_details = serializers.SerializerMethodField(read_only=True)
    category_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ChatSessionInvoice
        fields = '__all__'
        read_only_fields = ['invoice_number', 'status', 'created_at', 'updated_at']

    def get_buyer_details(self, obj):
        if obj.session and obj.session.buyer:
            return UserSerializer(obj.session.buyer, context=self.context).data
        return None

    def get_seller_details(self, obj):
        if obj.session and obj.session.seller:
            if obj.session.chat_type == 'VENDOR' and hasattr(obj.session.seller, 'vendor_shop_profile'):
                return ShopProfileSerializer(obj.session.seller.vendor_shop_profile, context=self.context).data
            elif obj.session.chat_type == 'SERVICE' and hasattr(obj.session.seller, 'business_profile'):
                return ServiceProviderBusinessProfileSerializer(obj.session.seller.business_profile, context=self.context).data
            return UserSerializer(obj.session.seller, context=self.context).data
        return None

    def get_category_details(self, obj):
        if obj.category:
            return CategorySerializer(obj.category, context=self.context).data
        return None

class PolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = Policy
        fields = '__all__'
