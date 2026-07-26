from django.contrib import admin
from .models import ActiveUser, ActiveCustomer, BroadcastAnnouncement
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
