from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem, VendorOrder, DeliveryCharge
from products.serializers import ProductSerializer

class DeliveryChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryCharge
        fields = '__all__'

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
    user_name = serializers.CharField(source='user.first_name', read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'user_name', 'items', 'total_amount', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']

    def get_total_amount(self, obj):
        return sum(item.quantity * item.unit_price for item in obj.items.all())

class OrderItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    product_name = serializers.CharField(source='product.title', read_only=True)
    shop_name = serializers.CharField(source='shop.shop_name', read_only=True)
    subtotal_price = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'product', 'product_name', 'product_details', 'shop', 'shop_name', 'quantity', 'unit_price', 'subtotal_price', 'vendor_order']
        read_only_fields = ['order', 'shop']

    def get_subtotal_price(self, obj):
        return obj.quantity * obj.unit_price

class VendorOrderSerializer(serializers.ModelSerializer):
    vendor_order_items = OrderItemSerializer(many=True, read_only=True)
    vendor_details = serializers.SerializerMethodField()
    buyer_details = serializers.SerializerMethodField()
    payment_method = serializers.CharField(source='parent_order.payment_method', read_only=True)
    payment_status = serializers.CharField(source='parent_order.payment_status', read_only=True)
    grand_total = serializers.SerializerMethodField()
    
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

    def get_grand_total(self, obj):
        return obj.subtotal_amount + obj.delivery_charge

class OrderSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source='buyer.full_name', read_only=True)
    buyer_city_name = serializers.CharField(source='buyer_city.name', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    vendor_orders = VendorOrderSerializer(many=True, read_only=True)
    delivery_charge_breakdown = serializers.SerializerMethodField()
    grand_total = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['buyer', 'order_number', 'total_amount', 'status', 'payment_status', 'rejection_reason', 'created_at', 'updated_at']

    def get_delivery_charge_breakdown(self, obj):
        from .models import DeliveryCharge
        breakdown = []
        delivery_rates = DeliveryCharge.objects.first()
        if not delivery_rates:
            return breakdown
            
        unique_shops = set(item.shop for item in obj.items.all() if item.shop)
        for shop in unique_shops:
            if shop.city_id and obj.buyer_city_id and str(shop.city_id) == str(obj.buyer_city_id):
                charge = delivery_rates.inside_city
            else:
                charge = delivery_rates.outside_city
                
            breakdown.append({
                "shop_name": shop.shop_name,
                "delivery_charge": charge
            })
            
        return breakdown

    def get_grand_total(self, obj):
        return obj.total_amount + obj.total_delivery_charge

from .models import OrderCommission

class OrderCommissionSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source='order_item.product.title', read_only=True)
    quantity = serializers.IntegerField(source='order_item.quantity', read_only=True)
    
    order_details = serializers.SerializerMethodField()
    buyer_details = serializers.SerializerMethodField()
    vendor_details = serializers.SerializerMethodField()
    calculation_details = serializers.SerializerMethodField()

    class Meta:
        model = OrderCommission
        fields = ['id', 'order_item', 'product_title', 'quantity', 'commission_amount', 
                  'order_details', 'buyer_details', 'vendor_details', 'calculation_details', 
                  'created_at', 'updated_at']

    def get_order_details(self, obj):
        order = obj.order_item.order
        return {
            "order_number": order.order_number,
            "status": order.status,
            "payment_method": order.payment_method,
            "payment_status": order.payment_status
        }

    def get_buyer_details(self, obj):
        buyer = obj.order_item.order.buyer
        return {
            "id": buyer.id,
            "full_name": buyer.full_name,
            "phone_number": buyer.phone_number,
            "shipping_address": obj.order_item.order.shipping_address
        }

    def get_vendor_details(self, obj):
        shop = obj.order_item.shop
        return {
            "id": shop.id,
            "shop_name": shop.shop_name,
            "shop_address": shop.shop_address,
            "owner_phone": shop.user.phone_number if shop.user else None
        }

    def get_calculation_details(self, obj):
        if obj.applied_percentage > 0:
            return {
                "type": "PERCENTAGE",
                "rate": str(obj.applied_percentage),
                "formula": "(Unit Price * Quantity) * Percentage",
                "calculation": f"({obj.order_item.unit_price} * {obj.order_item.quantity}) * {obj.applied_percentage}% = {obj.commission_amount}"
            }
        elif obj.applied_flat > 0:
            return {
                "type": "FLAT",
                "rate": str(obj.applied_flat),
                "formula": "Flat Rate * Quantity",
                "calculation": f"{obj.applied_flat} * {obj.order_item.quantity} = {obj.commission_amount}"
            }
        return {
            "type": "NONE",
            "rate": "0.00",
            "formula": "No commission setting found",
            "calculation": "0.00"
        }
