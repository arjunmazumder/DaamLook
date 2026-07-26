from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product
from vendors.models import ShopProfile

User = get_user_model()

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.phone_number}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.quantity} x {self.product.title} in Cart {self.cart.id}"

class Order(models.Model):
    STATUS_CHOICES = (
        ('PENDING_ADMIN_APPROVAL', 'Pending Admin Approval'),
        ('APPROVED', 'Approved (Sent to Vendor)'),
        ('REJECTED', 'Rejected'),
    )
    PAYMENT_METHOD_CHOICES = (
        ('COD', 'Cash on Delivery'),
        ('ONLINE', 'Online Payment'),
    )
    PAYMENT_STATUS_CHOICES = (
        ('UNPAID', 'Unpaid'),
        ('PAID', 'Paid'),
    )
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=50, unique=True, blank=True)
    
    # Shipping details
    shipping_address = models.TextField()
    contact_phone = models.CharField(max_length=20)
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING_ADMIN_APPROVAL')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='COD')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='UNPAID')
    
    rejection_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.order_number:
            self.order_number = f"ORD-{self.id:06d}"
            super().save(update_fields=['order_number'])

    def __str__(self):
        return f"Order {self.order_number} by {self.buyer.phone_number}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    shop = models.ForeignKey(ShopProfile, on_delete=models.CASCADE, related_name='order_items')
    
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Optional VendorOrder connection if we link OrderItem to VendorOrder directly
    vendor_order = models.ForeignKey('VendorOrder', on_delete=models.SET_NULL, null=True, blank=True, related_name='vendor_order_items')

    def __str__(self):
        product_title = self.product.title if self.product else "Deleted Product"
        return f"{self.quantity} x {product_title} in Order {self.order.order_number}"

class VendorOrder(models.Model):
    STATUS_CHOICES = (
        ('PROCESSING', 'Processing'),
        ('PACKED', 'Packed'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    )
    parent_order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='vendor_orders')
    vendor_shop = models.ForeignKey(ShopProfile, on_delete=models.CASCADE, related_name='received_orders')
    
    vendor_order_number = models.CharField(max_length=50, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PROCESSING')
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.vendor_order_number:
            self.vendor_order_number = f"VORD-{self.id:06d}"
            super().save(update_fields=['vendor_order_number'])

    def __str__(self):
        return f"Vendor Order {self.vendor_order_number} for {self.vendor_shop.shop_name}"
