from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=2000.00, help_text="Maximum negative balance allowed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        should_block = self.balance < -self.credit_limit
        
        # Check and update vendor shop profile
        if hasattr(self.user, 'vendor_shop_profile'):
            profile = self.user.vendor_shop_profile
            if profile.is_blocked != should_block:
                profile.is_blocked = should_block
                profile.save(update_fields=['is_blocked', 'updated_at'])

        # Check and update service provider business profile
        if hasattr(self.user, 'business_profile'):
            profile = self.user.business_profile
            if profile.is_blocked != should_block:
                profile.is_blocked = should_block
                profile.save(update_fields=['is_blocked', 'updated_at'])

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Wallet for {self.user} - Balance: {self.balance}"


class WalletTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = (
        ('IN', 'Credit (In)'),
        ('OUT', 'Debit (Out)'),
        ('DISCOUNT', 'Discount (In)'),
    )

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    order_commission = models.ForeignKey('orders.OrderCommission', on_delete=models.SET_NULL, null=True, blank=True, related_name='wallet_transactions')
    service_commission = models.ForeignKey('services.ServiceCommission', on_delete=models.SET_NULL, null=True, blank=True, related_name='wallet_transactions')
    chat_session_commission = models.ForeignKey('orders.ChatSessionInvoiceCommission', on_delete=models.SET_NULL, null=True, blank=True, related_name='wallet_transactions')
    
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} of {self.amount} for {self.wallet.user}"
