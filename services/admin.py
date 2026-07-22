from django.contrib import admin
from .models import (
    ServiceCategory,
    ServiceProviderBusinessProfile,
    ChatSession,
    ChatMessage,
    ServiceBooking,
    ServiceProviderNotification,
    ServiceProviderReview,
    ServiceInvoice
)

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    search_fields = ('name',)
    list_filter = ('is_active',)

@admin.register(ServiceProviderBusinessProfile)
class ServiceProviderBusinessProfileAdmin(admin.ModelAdmin):
    list_display = ('shop_name', 'provider', 'contact_number', 'average_rating')
    search_fields = ('shop_name', 'contact_number', 'provider__phone_number')

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'provider', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('buyer__phone_number', 'provider__shop_name')

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'sender', 'message_type', 'is_read', 'timestamp')
    list_filter = ('message_type', 'is_read')
    search_fields = ('message', 'sender__phone_number')

@admin.register(ServiceBooking)
class ServiceBookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'provider', 'status', 'payment_status', 'service_bill', 'created_at')
    list_filter = ('status', 'payment_status')
    search_fields = ('id', 'buyer__phone_number', 'provider__shop_name')

@admin.register(ServiceProviderNotification)
class ServiceProviderNotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'provider', 'is_read', 'created_at')
    list_filter = ('is_read',)

@admin.register(ServiceProviderReview)
class ServiceProviderReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'reviewer', 'reviewee', 'rating_stars', 'bill_rating', 'on_time_delivery_rating', 'response_and_behavior_rating', 'honesty_rating', 'created_at')
    list_filter = ('rating_stars', 'bill_rating', 'on_time_delivery_rating', 'response_and_behavior_rating', 'honesty_rating')
    readonly_fields = ('rating_stars',)

@admin.register(ServiceInvoice)
class ServiceInvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'booking', 'total_amount', 'payment_status', 'payment_method', 'created_at')
    list_filter = ('payment_status', 'payment_method')
    search_fields = ('invoice_number', 'transaction_id', 'booking__buyer__phone_number')
    readonly_fields = ('invoice_number', 'total_amount', 'paid_at')
