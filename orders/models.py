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
    buyer_city = models.ForeignKey('vendors.City', on_delete=models.SET_NULL, null=True, blank=True)
    order_number = models.CharField(max_length=50, unique=True, blank=True)
    
    # Shipping details
    shipping_address = models.TextField()
    contact_phone = models.CharField(max_length=20)
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING_ADMIN_APPROVAL')
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
            
        # --- COMMISSION AND VENDOR ORDER LOGIC ---
        if self.status == 'APPROVED':
            from core.models import Commission
            from decimal import Decimal
            from .models import OrderCommission, VendorOrder, DeliveryCharge
            
            # --- VENDOR ORDER CREATION ---
            if not self.vendor_orders.exists():
                shop_items = {}
                for item in self.items.all():
                    if item.shop not in shop_items:
                        shop_items[item.shop] = []
                    shop_items[item.shop].append(item)

                delivery_rates = DeliveryCharge.objects.first()

                for shop, items in shop_items.items():
                    subtotal = sum(i.quantity * i.unit_price for i in items)
                    
                    delivery_charge = Decimal('0.00')
                    if delivery_rates:
                        if shop.city_id and str(shop.city_id) == str(self.buyer_city_id):
                            delivery_charge = Decimal(str(delivery_rates.inside_city))
                        else:
                            delivery_charge = Decimal(str(delivery_rates.outside_city))
                            
                    vendor_order = VendorOrder.objects.create(
                        parent_order=self,
                        vendor_shop=shop,
                        subtotal_amount=subtotal,
                        delivery_charge=delivery_charge,
                        status='PROCESSING'
                    )
                    
                    for item in items:
                        item.vendor_order = vendor_order
                        item.save(update_fields=['vendor_order'])
                        
                        # Deduct stock ONLY upon approval
                        if item.product:
                            item.product.stock_quantity -= item.quantity
                            item.product.save(update_fields=['stock_quantity', 'updated_at'])
            
            # --- COMMISSION LOGIC ---
            
            for item in self.items.all():
                commission_setting = None
                if item.product and item.product.category:
                    commission_setting = Commission.objects.filter(category=item.product.category).first()
                    
                if not commission_setting:
                    commission_setting = Commission.objects.filter(category__isnull=True, servicecategory__isnull=True).first()
                    
                calculated_commission = Decimal('0.00')
                if commission_setting:
                    item_total = item.unit_price * item.quantity
                    
                    if commission_setting.percentage and commission_setting.percentage > 0:
                        calculated_commission = (item_total * commission_setting.percentage) / Decimal('100.00')
                    elif commission_setting.flat and commission_setting.flat > 0:
                        calculated_commission = commission_setting.flat * item.quantity
                        
                order_comm, created = OrderCommission.objects.get_or_create(order_item=item)
                
                new_applied_pct = commission_setting.percentage if commission_setting and commission_setting.percentage else Decimal('0.00')
                new_applied_flat = commission_setting.flat if commission_setting and commission_setting.flat else Decimal('0.00')
                
                if Decimal(str(order_comm.commission_amount)) != calculated_commission or Decimal(str(order_comm.applied_percentage)) != new_applied_pct or Decimal(str(order_comm.applied_flat)) != new_applied_flat:
                    current_comm = Decimal(str(order_comm.commission_amount))
                    difference = calculated_commission - current_comm
                    order_comm.commission_amount = calculated_commission
                    order_comm.applied_percentage = new_applied_pct
                    order_comm.applied_flat = new_applied_flat
                    order_comm.save(update_fields=['commission_amount', 'applied_percentage', 'applied_flat', 'updated_at'])
                    
                    if difference != Decimal('0.00') and item.shop and item.shop.user:
                        from wallets.models import Wallet, WalletTransaction
                        wallet, _ = Wallet.objects.get_or_create(user=item.shop.user)
                        
                        current_balance = Decimal(str(wallet.balance))
                        wallet.balance = current_balance - difference
                        wallet.save(update_fields=['balance', 'updated_at'])
                        WalletTransaction.objects.create(
                            wallet=wallet,
                            transaction_type='OUT' if difference > 0 else 'IN',
                            amount=abs(difference),
                            order_commission=order_comm,
                            description=f"Commission adjustment for Order {self.order_number}"
                        )

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
    vendor_shop = models.ForeignKey(ShopProfile, on_delete=models.CASCADE, related_name='vendor_orders')
    
    vendor_order_number = models.CharField(max_length=50, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PROCESSING')
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.vendor_order_number:
            self.vendor_order_number = f"VORD-{self.id:06d}"
            super().save(update_fields=['vendor_order_number'])

    def __str__(self):
        return f"Vendor Order {self.vendor_order_number} for {self.vendor_shop.shop_name}"

class DeliveryCharge(models.Model):
    inside_city = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    outside_city = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Delivery Charges"

    def __str__(self):
        return f"Inside City: {self.inside_city}, Outside City: {self.outside_city}"

class OrderCommission(models.Model): 
    order_item = models.OneToOneField('OrderItem', on_delete=models.CASCADE, related_name='commission_record')
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    applied_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    applied_flat = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Commission for Item {self.order_item.id} - {self.commission_amount}"

class ChatSessionInvoice(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('REJECTED', 'Rejected'),
    )

    invoice_number = models.CharField(max_length=50, unique=True, blank=True)
    session = models.ForeignKey('core.GlobalChatSession', on_delete=models.CASCADE, related_name='invoices')
    category = models.ForeignKey('products.Category', on_delete=models.SET_NULL, null=True, blank=True)
    
    product_name = models.CharField(max_length=255)
    price_per_one_pice = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1)
    
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    after_discount_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    shipping_address = models.TextField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        from decimal import Decimal
        
        # Auto calculate total price
        price = Decimal(str(self.price_per_one_pice or '0.00'))
        qty = Decimal(str(self.quantity or '0'))
        self.total_price = price * qty
        
        # Auto calculate after discount
        discount = Decimal(str(self.discount_amount or '0.00'))
        self.after_discount_price = max(Decimal('0.00'), self.total_price - discount)

        super().save(*args, **kwargs)

        # Generate invoice number if not set
        if not self.invoice_number:
            self.invoice_number = f"CINV-{self.id:06d}"
            super().save(update_fields=['invoice_number'])

        # If it's a new invoice, push a message to chat
        if is_new:
            from core.models import GlobalChatMessage
            # Determine sender (usually the seller in the session)
            GlobalChatMessage.objects.create(
                session=self.session,
                sender=self.session.seller,
                message_type='INVOICE',
                message=f"Invoice {self.invoice_number} created for {self.product_name}."
            )

        # Handle Commission on CONFIRM
        if self.status == 'CONFIRMED':
            from core.models import Commission
            
            commission_setting = Commission.objects.filter(category=self.category).first() if self.category else None
            if not commission_setting:
                commission_setting = Commission.objects.filter(category__isnull=True, servicecategory__isnull=True).first()
                
            calculated_commission = Decimal('0.00')
            applied_pct = Decimal('0.00')
            applied_flat = Decimal('0.00')
            
            if commission_setting:
                if commission_setting.percentage and commission_setting.percentage > 0:
                    calculated_commission = (self.after_discount_price * commission_setting.percentage) / Decimal('100.00')
                    applied_pct = commission_setting.percentage
                elif commission_setting.flat and commission_setting.flat > 0:
                    calculated_commission = commission_setting.flat
                    applied_flat = commission_setting.flat
                    
            chat_comm, created = ChatSessionInvoiceCommission.objects.get_or_create(invoice=self)
            
            if Decimal(str(chat_comm.commission_amount)) != calculated_commission:
                difference = calculated_commission - Decimal(str(chat_comm.commission_amount))
                chat_comm.commission_amount = calculated_commission
                chat_comm.applied_percentage = applied_pct
                chat_comm.applied_flat = applied_flat
                chat_comm.save(update_fields=['commission_amount', 'applied_percentage', 'applied_flat', 'updated_at'])
                
                if difference != Decimal('0.00') and self.session and self.session.seller:
                    from wallets.models import Wallet, WalletTransaction
                    wallet, _ = Wallet.objects.get_or_create(user=self.session.seller)
                    wallet.balance -= difference
                    wallet.save(update_fields=['balance', 'updated_at'])
                    
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        transaction_type='OUT' if difference > 0 else 'IN',
                        amount=abs(difference),
                        chat_session_commission=chat_comm,
                        description=f"Commission adjustment for Chat Invoice {self.invoice_number}"
                    )

    def __str__(self):
        return f"Chat Invoice {self.invoice_number}"

class ChatSessionInvoiceCommission(models.Model):
    invoice = models.OneToOneField(ChatSessionInvoice, on_delete=models.CASCADE, related_name='commission_record')
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    applied_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    applied_flat = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Commission for {self.invoice.invoice_number} - {self.commission_amount}"

