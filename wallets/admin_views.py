from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from drf_yasg.utils import swagger_auto_schema
from django.utils.decorators import method_decorator
from .models import Wallet, WalletTransaction
from .serializers import WalletSerializer, WalletTransactionSerializer

@method_decorator(name='list', decorator=swagger_auto_schema(tags=['Wallets']))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=['Wallets']))
class AdminWalletViewSet(viewsets.ReadOnlyModelViewSet):
    """
    For Admins to view all wallets and their balances.
    """
    queryset = Wallet.objects.all().order_by('-created_at')
    serializer_class = WalletSerializer
    permission_classes = [IsAdminUser]

from drf_yasg import openapi
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

@method_decorator(name='list', decorator=swagger_auto_schema(
    tags=['Wallets'],
    manual_parameters=[
        openapi.Parameter('search', openapi.IN_QUERY, description="Search by description, phone number, or full name", type=openapi.TYPE_STRING),
        openapi.Parameter('transaction_type', openapi.IN_QUERY, description="Filter by IN, OUT, or DISCOUNT", type=openapi.TYPE_STRING)
    ]
))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=['Wallets']))
class AdminWalletTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    For Admins to view all wallet transactions system-wide.
    """
    queryset = WalletTransaction.objects.all().order_by('-created_at')
    serializer_class = WalletTransactionSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['transaction_type']
    search_fields = ['description', 'wallet__user__phone_number', 'wallet__user__full_name']
