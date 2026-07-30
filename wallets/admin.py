from django.contrib import admin
from .models import Wallet, WalletTransaction

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'credit_limit', 'created_at', 'updated_at')
    search_fields = ('user__phone_number', 'user__full_name')
    list_filter = ('created_at',)

@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'transaction_type', 'amount', 'discount', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('wallet__user__phone_number', 'reference', 'description')
    readonly_fields = ('created_at',)
