from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem, VendorOrder, DeliveryCharge, OrderCommission

@admin.register(DeliveryCharge)
class DeliveryChargeAdmin(admin.ModelAdmin):
    list_display = ['id', 'inside_city', 'outside_city']


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created_at', 'updated_at']
    search_fields = ['user__phone_number', 'user__email']
    inlines = [CartItemInline]

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    
class VendorOrderInline(admin.TabularInline):
    model = VendorOrder
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'buyer', 'status', 'total_amount', 'total_delivery_charge', 'payment_method', 'payment_status', 'created_at']
    list_filter = ['status', 'payment_method', 'payment_status', 'created_at']
    search_fields = ['order_number', 'buyer__phone_number', 'contact_phone']
    inlines = [OrderItemInline, VendorOrderInline]

@admin.register(VendorOrder)
class VendorOrderAdmin(admin.ModelAdmin):
    list_display = ['vendor_order_number', 'parent_order', 'vendor_shop', 'status', 'subtotal_amount', 'delivery_charge', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['vendor_order_number', 'parent_order__order_number', 'vendor_shop__shop_name']

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'cart', 'product', 'quantity', 'unit_price', 'created_at']
    
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'product', 'shop', 'quantity', 'unit_price']

@admin.register(OrderCommission)
class OrderCommissionAdmin(admin.ModelAdmin):
    list_display = ['order_item', 'commission_amount', 'created_at']
