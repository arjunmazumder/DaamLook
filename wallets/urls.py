from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MyWalletView, MyWalletTransactionsView
from .admin_views import AdminWalletViewSet, AdminWalletTransactionViewSet

router = DefaultRouter()
router.register(r'admin/all', AdminWalletViewSet, basename='admin-wallets-all')
router.register(r'admin/transactions', AdminWalletTransactionViewSet, basename='admin-wallets-transactions')

urlpatterns = [
    path('my-wallet/', MyWalletView.as_view(), name='my-wallet'),
    path('transactions/', MyWalletTransactionsView.as_view(), name='my-wallet-transactions'),
    path('', include(router.urls)),
]
