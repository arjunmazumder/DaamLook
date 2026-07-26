from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem, VendorOrder
from products.serializers import ProductSerializer

class CartItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    subtotal_price = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'product', 'product_details', 'quantity', 'unit_price', 'subtotal_price', 'created_at', 'updated_at']
        read_only_fields = ['cart', 'unit_price', 'created_at', 'updated_at']

    def get_subtotal_price(self, obj):
        return obj.quantity * obj.unit_price

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_amount', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']

    def get_total_amount(self, obj):
        return sum(item.quantity * item.unit_price for item in obj.items.all())

class OrderItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    subtotal_price = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'product', 'product_details', 'shop', 'quantity', 'unit_price', 'subtotal_price', 'vendor_order']
        read_only_fields = ['order', 'shop']

    def get_subtotal_price(self, obj):
        return obj.quantity * obj.unit_price

class VendorOrderSerializer(serializers.ModelSerializer):
    vendor_order_items = OrderItemSerializer(many=True, read_only=True)
    vendor_details = serializers.SerializerMethodField()
    buyer_details = serializers.SerializerMethodField()
    payment_method = serializers.CharField(source='parent_order.payment_method', read_only=True)
    payment_status = serializers.CharField(source='parent_order.payment_status', read_only=True)
    
    class Meta:
        model = VendorOrder
        fields = '__all__'
        read_only_fields = ['parent_order', 'vendor_shop', 'vendor_order_number', 'subtotal_amount', 'created_at', 'updated_at']

    def get_vendor_details(self, obj):
        shop = obj.vendor_shop
        return {
            "id": shop.id,
            "shop_name": shop.shop_name,
            "shop_address": shop.shop_address,
            "contact_email": shop.contact_email,
            "owner_phone": shop.user.phone_number
        }

    def get_buyer_details(self, obj):
        buyer = obj.parent_order.buyer
        return {
            "id": buyer.id,
            "full_name": buyer.full_name,
            "phone_number": buyer.phone_number,
            "shipping_address": obj.parent_order.shipping_address,
            "contact_phone": obj.parent_order.contact_phone
        }

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    vendor_orders = VendorOrderSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['buyer', 'order_number', 'total_amount', 'status', 'payment_status', 'rejection_reason', 'created_at', 'updated_at']
