from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='subcategory_images/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Sub Categories"

    def __str__(self):
        return f"{self.category.name} -> {self.name}"


class Product(models.Model):
    PRODUCT_TYPE_CHOICES = (
        ('RETAIL', 'Retail'),
        ('WHOLESALE', 'Wholesale'),
    )

    DISCOUNT_TYPE_CHOICES = (
        ('NONE', 'None'),
        ('FLAT', 'Flat'),
        ('PERCENTAGE', 'Percentage'),
    )

    APPROVAL_STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    shop = models.ForeignKey('vendors.ShopProfile', on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, default='RETAIL')
    stock_quantity = models.IntegerField(default=0)
    
    retail_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    base_wholesale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    moq = models.IntegerField("Minimum Order Quantity (MOQ)", default=1, help_text="Minimum amount a user must purchase (especially for wholesale)")
    
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='NONE')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_start_date = models.DateTimeField(null=True, blank=True)
    discount_end_date = models.DateTimeField(null=True, blank=True)
    
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS_CHOICES, default='PENDING')
    rejection_reason = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class BulkPricingTier(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bulk_pricing_tiers')
    min_quantity = models.IntegerField()
    max_quantity = models.IntegerField()
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.title}: {self.min_quantity}-{self.max_quantity} units at {self.price_per_unit}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.title} (Primary: {self.is_primary})"
