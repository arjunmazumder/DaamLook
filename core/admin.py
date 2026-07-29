from django.contrib import admin
from .models import ActiveUser, ActiveCustomer, BroadcastAnnouncement, Commission

@admin.register(ActiveUser)
class ActiveUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'latitude', 'longitude', 'updated_at')
    search_fields = ('user__phone_number',)
    list_filter = ('updated_at',)

@admin.register(ActiveCustomer)
class ActiveCustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'category', 'latitude', 'longitude', 'updated_at')
    search_fields = ('user__phone_number', 'category__name')
    list_filter = ('updated_at',)

@admin.register(BroadcastAnnouncement)
class BroadcastAnnouncementAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'target_audience', 'created_at')
    search_fields = ('title', 'message')
    list_filter = ('target_audience', 'created_at')
    filter_horizontal = ('specific_targets',)

@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'servicecategory', 'percentage', 'flat', 'created_at')
    list_filter = ('category', 'servicecategory', 'created_at')
    search_fields = ('category__name', 'servicecategory__name')

from .models import GlobalChatSession, GlobalChatMessage

@admin.register(GlobalChatSession)
class GlobalChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'seller', 'chat_type', 'is_active', 'updated_at')
    list_filter = ('chat_type', 'is_active')
    search_fields = ('buyer__phone_number', 'seller__phone_number')

@admin.register(GlobalChatMessage)
class GlobalChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'sender', 'message_type', 'is_read', 'timestamp')
    list_filter = ('message_type', 'is_read')
    search_fields = ('message', 'sender__phone_number')
