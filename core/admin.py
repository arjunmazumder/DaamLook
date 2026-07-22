from django.contrib import admin
from .models import ActiveUser, ActiveCustomer

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
