from django.contrib import admin
from .models import Category, SubCategory, Product, ProductImage, BulkPricingTier

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
    search_fields = ('name', 'description')

@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'created_at')
    search_fields = ('name', 'description', 'category__name')
    list_filter = ('category',)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class BulkPricingTierInline(admin.TabularInline):
    model = BulkPricingTier
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'shop', 'product_type', 'approval_status', 'is_active', 'created_at')
    list_filter = ('product_type', 'approval_status', 'is_active')
    search_fields = ('title', 'shop__shop_name')
    inlines = [ProductImageInline, BulkPricingTierInline]
