from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    icon_img = models.ImageField(upload_to='services/categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ServiceProviderBusinessProfile(models.Model):
    provider = models.OneToOneField(User, on_delete=models.CASCADE, related_name='business_profile')
    shop_name = models.CharField(max_length=255)
    contact_number = models.CharField(max_length=20)
    address = models.TextField(blank=True, null=True)
    categories = models.ManyToManyField(ServiceCategory, related_name='providers')
    average_rating = models.FloatField(default=0.0)
    total_reviews = models.IntegerField(default=0)
    admin_rating_adjustment = models.FloatField(default=0.0, help_text="Manual rating adjustment by admin")
    about_me = models.TextField(blank=True, null=True)
    work_day = models.CharField(max_length=100, blank=True, null=True)
    available_time = models.CharField(max_length=100, blank=True, null=True)
    total_complete_worked = models.IntegerField(default=0)
    is_blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.shop_name

class Recentwork(models.Model):
    provider = models.ForeignKey(ServiceProviderBusinessProfile, on_delete=models.CASCADE, related_name='recent_works')
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='services/recent_works/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class ServiceBooking(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Provider Approval'),
        ('CONFIRMED', 'Confirmed & Coming'),
        ('IN_PROGRESS', 'Work In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )
    PAYMENT_STATUS_CHOICES = (
        ('UNPAID', 'Unpaid'),
        ('PAID', 'Paid'),
    )
    # service_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_bookings')
    provider = models.ForeignKey(ServiceProviderBusinessProfile, on_delete=models.CASCADE, related_name='received_bookings')
    chat_session = models.OneToOneField('core.GlobalChatSession', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoice_booking')
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True, related_name='bookings')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='UNPAID')
    service_bill = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    service_description = models.TextField(blank=True, null=True)
    scheduled_date = models.DateField(blank=True, null=True)
    scheduled_time = models.TimeField(blank=True, null=True)
    # buyer_latitude = models.FloatField(blank=True, null=True)
    # buyer_longitude = models.FloatField(blank=True, null=True)
    cancellation_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # def save(self, *args, **kwargs):
    #     super().save(*args, **kwargs)
    #     if not self.service_number:
    #         self.service_number = f"#SER-{self.id:04d}"
    #         super().save(update_fields=['service_number'])

    def __str__(self):
        return f"Booking {self.id} - {self.buyer.phone_number} to {self.provider.shop_name}"

class ServiceProviderNotification(models.Model):
    provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    booking = models.ForeignKey(ServiceBooking, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.provider.phone_number}"

class ServiceProviderReview(models.Model):
    booking = models.OneToOneField(ServiceBooking, on_delete=models.CASCADE, related_name='review')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reviews')
    reviewee = models.ForeignKey(ServiceProviderBusinessProfile, on_delete=models.CASCADE, related_name='received_reviews')
    
    bill_rating = models.IntegerField(default=5)
    on_time_delivery_rating = models.IntegerField(default=5)
    response_and_behavior_rating = models.IntegerField(default=5)
    honesty_rating = models.IntegerField(default=5)
    
    rating_stars = models.FloatField(default=5.0)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.rating_stars = round(
            (self.bill_rating + self.on_time_delivery_rating + self.response_and_behavior_rating + self.honesty_rating) / 4.0,
            2
        )
        super().save(*args, **kwargs)

        provider = self.reviewee
        reviews = provider.received_reviews.all()
        total = reviews.count()
        if total > 0:
            avg = sum(r.rating_stars for r in reviews) / float(total)
            provider.total_reviews = total
            provider.average_rating = min(max(round(avg + provider.admin_rating_adjustment, 2), 0.0), 5.0)
            provider.save(update_fields=['total_reviews', 'average_rating', 'updated_at'])

    def delete(self, *args, **kwargs):
        provider = self.reviewee
        super().delete(*args, **kwargs)
        reviews = provider.received_reviews.all()
        total = reviews.count()
        if total > 0:
            avg = sum(r.rating_stars for r in reviews) / float(total)
            provider.total_reviews = total
            provider.average_rating = min(max(round(avg + provider.admin_rating_adjustment, 2), 0.0), 5.0)
        else:
            provider.total_reviews = 0
            provider.average_rating = min(max(round(0.0 + provider.admin_rating_adjustment, 2), 0.0), 5.0)
        provider.save(update_fields=['total_reviews', 'average_rating', 'updated_at'])

    def __str__(self):
        return f"Review for {self.reviewee.shop_name} by {self.reviewer.phone_number}"

class ServiceInvoice(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('UNPAID', 'Unpaid'),
        ('PARTIAL', 'Partially Paid'),
        ('PAID', 'Paid'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('CASH', 'Cash on Delivery'),
        ('BKASH', 'bKash'),
        ('NAGAD', 'Nagad'),
        ('CARD', 'Credit/Debit Card'),
    )

    booking = models.OneToOneField(ServiceBooking, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=50, unique=True, blank=True)
    
    base_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    extra_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    extra_charges_note = models.TextField(blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default='PAID')
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        # Auto-fetch base_amount from booking.service_bill if not set
        if self.booking and (not self.base_amount or self.base_amount == 0):
            if self.booking.service_bill and self.booking.service_bill > 0:
                self.base_amount = self.booking.service_bill

        from decimal import Decimal
        base = Decimal(str(self.base_amount or '0.00'))
        extra = Decimal(str(self.extra_charges or '0.00'))
        discount = Decimal(str(self.discount_amount or '0.00'))
        calculated_total = base + extra - discount
        self.total_amount = max(Decimal('0.00'), calculated_total)

        if self.payment_status == 'PAID' and not self.paid_at:
            from django.utils import timezone
            self.paid_at = timezone.now()

        super().save(*args, **kwargs)

        if is_new and self.booking and self.booking.provider:
            self.booking.provider.total_complete_worked += 1
            self.booking.provider.save(update_fields=['total_complete_worked', 'updated_at'])

        if not self.invoice_number:
            self.invoice_number = f"INV-{self.id:04d}"
            super().save(update_fields=['invoice_number'])

        if self.booking:
            booking_updated = False
            if self.booking.service_bill != self.total_amount:
                self.booking.service_bill = self.total_amount
                booking_updated = True
            if self.payment_status == 'PAID' and self.booking.payment_status != 'PAID':
                self.booking.payment_status = 'PAID'
                booking_updated = True
            if booking_updated:
                self.booking.save(update_fields=['service_bill', 'payment_status', 'updated_at'])

        # --- COMMISSION LOGIC ---
        from core.models import Commission
        from decimal import Decimal
        
        commission_setting = None
        if self.booking and self.booking.category:
            commission_setting = Commission.objects.filter(servicecategory=self.booking.category).first()
            
        if not commission_setting:
            commission_setting = Commission.objects.filter(category__isnull=True, servicecategory__isnull=True).first()
            
        calculated_commission = Decimal('0.00')
        if commission_setting:
            if commission_setting.percentage and commission_setting.percentage > 0:
                calculated_commission = (self.total_amount * commission_setting.percentage) / Decimal('100.00')
            elif commission_setting.flat and commission_setting.flat > 0:
                calculated_commission = commission_setting.flat
                
        service_comm, created = ServiceCommission.objects.get_or_create(invoice=self)
        if service_comm.commission_amount != calculated_commission:
            difference = calculated_commission - service_comm.commission_amount
            service_comm.commission_amount = calculated_commission
            service_comm.save(update_fields=['commission_amount', 'updated_at'])
            
            if difference != Decimal('0.00') and self.booking and self.booking.provider and self.booking.provider.provider:
                from wallets.models import Wallet, WalletTransaction
                wallet, _ = Wallet.objects.get_or_create(user=self.booking.provider.provider)
                wallet.balance -= difference
                wallet.save(update_fields=['balance', 'updated_at'])
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='OUT' if difference > 0 else 'IN',
                    amount=abs(difference),
                    service_commission=service_comm,
                    description=f"Commission adjustment for Service Invoice {self.invoice_number}"
                )

    def __str__(self):
        return f"{self.invoice_number} for Booking {self.booking.id}"

class ServiceCommission(models.Model):
    invoice = models.OneToOneField(ServiceInvoice, on_delete=models.CASCADE, related_name='commission_record')
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Commission for {self.invoice.invoice_number} - {self.commission_amount}"
