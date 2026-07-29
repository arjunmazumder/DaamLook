from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class City(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Cities"
        ordering = ['name']

    def __str__(self):
        return self.name

class ShopProfile(models.Model):
    SHOP_TYPE_CHOICES = (
        ('RETAILER', 'Retailer'),
        ('WHOLESALER', 'Wholesaler'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_shop_profile')
    shop_type = models.CharField(max_length=20, choices=SHOP_TYPE_CHOICES, default='RETAILER')
    
    shop_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='shop/logos/', blank=True, null=True)
    banner = models.ImageField(upload_to='shop/banners/', blank=True, null=True)
    
    contact_email = models.EmailField(blank=True, null=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, related_name='shops')
    shop_address = models.TextField()

    trade_license_number = models.CharField(max_length=100, blank=True, null=True)
    trade_license_document = models.FileField(upload_to='shop/documents/', blank=True, null=True)

    opening_time = models.TimeField(blank=True, null=True)
    closing_time = models.TimeField(blank=True, null=True)

    average_rating = models.FloatField(default=0.0)
    total_reviews = models.IntegerField(default=0)
    admin_rating_adjustment = models.FloatField(default=0.0, help_text="Manual rating adjustment by admin")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.shop_name} ({self.shop_type})"


class ShopReview(models.Model):
    shop = models.ForeignKey(ShopProfile, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shop_reviews_given')
    
    product_rating = models.IntegerField(default=5)       
    price_rating = models.IntegerField(default=5)         
    on_time_delivery_rating = models.IntegerField(default=5)      
    response_and_behavior_rating = models.IntegerField(default=5)      
    
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def average_rating(self):
        return round(
            (self.product_rating + self.price_rating + self.on_time_delivery_rating + self.response_and_behavior_rating) / 4.0,
            2
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        reviews = self.shop.reviews.all()
        total = reviews.count()
        if total > 0:
            avg = sum(r.average_rating for r in reviews) / float(total)
            self.shop.total_reviews = total
            self.shop.average_rating = min(max(round(avg + self.shop.admin_rating_adjustment, 2), 0.0), 5.0)
            self.shop.save(update_fields=['total_reviews', 'average_rating', 'updated_at'])

    def delete(self, *args, **kwargs):
        shop = self.shop
        super().delete(*args, **kwargs)
        reviews = shop.reviews.all()
        total = reviews.count()
        if total > 0:
            avg = sum(r.average_rating for r in reviews) / float(total)
            shop.total_reviews = total
            shop.average_rating = min(max(round(avg + shop.admin_rating_adjustment, 2), 0.0), 5.0)
        else:
            shop.total_reviews = 0
            shop.average_rating = min(max(round(0.0 + shop.admin_rating_adjustment, 2), 0.0), 5.0)
        shop.save(update_fields=['total_reviews', 'average_rating', 'updated_at'])

    def __str__(self):
        return f"Review by {self.reviewer} for {self.shop.shop_name}"

class VendorChatSession(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_vendor_chats')
    vendor = models.ForeignKey(ShopProfile, on_delete=models.CASCADE, related_name='received_vendor_chats')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('buyer', 'vendor') 

    def __str__(self):
        # Fallback to username or email if phone_number doesn't exist
        buyer_identifier = getattr(self.buyer, 'phone_number', getattr(self.buyer, 'username', getattr(self.buyer, 'email', str(self.buyer.id))))
        return f"Chat between {buyer_identifier} & {self.vendor.shop_name}"


class VendorChatMessage(models.Model):
    MESSAGE_TYPE_CHOICES = (
        ('TEXT', 'Text'),
        ('IMAGE', 'Image'),
        ('SYSTEM_ALERT', 'System Alert'),
        ('INVOICE', 'Invoice'),
    )
    session = models.ForeignKey(VendorChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_vendor_messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='TEXT')
    message = models.TextField(blank=True, null=True)
    attachment = models.FileField(upload_to='vendors/chats/', blank=True, null=True)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Message {self.id} in Session {self.session_id}"
