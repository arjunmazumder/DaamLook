from django.contrib import admin
from .models import ShopProfile, ShopReview

@admin.register(ShopProfile)
class ShopProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'shop_name', 'shop_type', 'user', 'average_rating', 'total_reviews', 'created_at')
    list_filter = ('shop_type',)
    search_fields = ('shop_name', 'user__phone_number', 'contact_email')
    readonly_fields = ('average_rating', 'total_reviews', 'created_at', 'updated_at')

@admin.register(ShopReview)
class ShopReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'shop', 'reviewer', 'average_rating', 'product_rating', 'price_rating', 'on_time_delivery_rating', 'response_and_behavior_rating', 'created_at')
    list_filter = ('product_rating', 'price_rating', 'on_time_delivery_rating', 'response_and_behavior_rating')
    search_fields = ('shop__shop_name', 'reviewer__phone_number', 'comment')
