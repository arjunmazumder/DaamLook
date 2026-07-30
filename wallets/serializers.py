from rest_framework import serializers
from .models import Wallet, WalletTransaction

class WalletSerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField()
    shop_profile = serializers.SerializerMethodField()
    service_profile = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = ['id', 'balance', 'credit_limit', 'created_at', 'updated_at', 'user_info', 'shop_profile', 'service_profile']
        read_only_fields = ['id', 'balance', 'credit_limit', 'created_at', 'updated_at']

    def get_user_info(self, obj):
        from users.serializers import UserWithProfileSerializer
        return UserWithProfileSerializer(obj.user).data

    def get_shop_profile(self, obj):
        if hasattr(obj.user, 'vendor_shop_profile'):
            from vendors.serializers import ShopProfileSerializer
            return ShopProfileSerializer(obj.user.vendor_shop_profile).data
        return None

    def get_service_profile(self, obj):
        if hasattr(obj.user, 'business_profile'):
            from services.serializers import ServiceProviderBusinessProfileSerializer
            return ServiceProviderBusinessProfileSerializer(obj.user.business_profile).data
        return None

class WalletTransactionSerializer(serializers.ModelSerializer):
    order_details = serializers.SerializerMethodField()
    service_details = serializers.SerializerMethodField()

    class Meta:
        model = WalletTransaction
        fields = [
            'id', 
            'transaction_type', 
            'amount', 
            'discount',
            'order_commission', 
            'service_commission', 
            'description', 
            'created_at',
            'order_details',
            'service_details'
        ]
        read_only_fields = fields

    def get_order_details(self, obj):
        if not obj.order_commission:
            return None
        item = obj.order_commission.order_item
        if not item:
            return None
            
        buyer = item.order.buyer
        vendor = item.shop
        
        return {
            'order_id': item.order.id,
            'order_number': item.order.order_number,
            'buyer': {
                'id': buyer.id,
                'name': buyer.full_name,
                'phone': buyer.phone_number
            },
            'vendor': {
                'id': vendor.id,
                'shop_name': vendor.shop_name
            },
            'item': {
                'product_name': item.product.title if item.product else 'Unknown',
                'quantity': item.quantity,
                'unit_price': str(item.unit_price)
            },
            'commission_applied': {
                'percentage': str(obj.order_commission.applied_percentage),
                'flat': str(obj.order_commission.applied_flat)
            }
        }

    def get_service_details(self, obj):
        if not obj.service_commission:
            return None
        invoice = obj.service_commission.invoice
        if not invoice or not invoice.booking:
            return None
            
        booking = invoice.booking
        buyer = booking.user
        provider = booking.provider
        
        return {
            'booking_id': booking.id,
            'invoice_number': invoice.invoice_number,
            'service_name': booking.service.title if booking.service else 'Unknown',
            'buyer': {
                'id': buyer.id,
                'name': buyer.full_name,
                'phone': buyer.phone_number
            },
            'provider': {
                'id': provider.id,
                'provider_name': provider.provider_name if hasattr(provider, 'provider_name') else 'Unknown'
            },
            'total_bill': str(invoice.total_amount)
        }
