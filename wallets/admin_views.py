from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from users.permissions import IsAdminOrSuperAdmin
from drf_yasg.utils import swagger_auto_schema
from django.utils.decorators import method_decorator
from django.db import transaction
from django.db.models import Q
from drf_yasg import openapi
from rest_framework import filters
from .models import Wallet, WalletTransaction
from .serializers import WalletSerializer, WalletTransactionSerializer, UpdateCreditLimitSerializer, AddDiscountSerializer

@method_decorator(name='list', decorator=swagger_auto_schema(tags=['Wallets']))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=['Wallets']))
class AdminWalletViewSet(viewsets.ReadOnlyModelViewSet):
    """
    For Admins to view all wallets and their balances.
    """
    queryset = Wallet.objects.all().order_by('-created_at')
    serializer_class = WalletSerializer
    permission_classes = [IsAdminOrSuperAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__phone_number', 'user__full_name', 'user__vendor_shop_profile__shop_name', 'user__business_profile__shop_name']

    @swagger_auto_schema(
        method='patch',
        tags=['Wallets'],
        operation_description="Update credit limit for a specific wallet",
        request_body=UpdateCreditLimitSerializer,
        responses={200: WalletSerializer()}
    )
    @action(detail=True, methods=['patch'], url_path='update-credit-limit')
    def update_credit_limit(self, request, pk=None):
        wallet = self.get_object()
        serializer = UpdateCreditLimitSerializer(wallet, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(WalletSerializer(wallet).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        method='post',
        tags=['Wallets'],
        operation_description="Add a discount to a specific wallet (increases the balance)",
        request_body=AddDiscountSerializer,
        responses={200: WalletSerializer()}
    )
    @action(detail=True, methods=['post'], url_path='add-discount')
    def add_discount(self, request, pk=None):
        wallet = self.get_object()
        serializer = AddDiscountSerializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            description = serializer.validated_data.get('description', 'Admin discount added')
            
            with transaction.atomic():
                wallet.balance += amount
                wallet.save(update_fields=['balance', 'updated_at'])
                
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='DISCOUNT',
                    amount=amount,
                    description=description
                )
                
            return Response(WalletSerializer(wallet).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BlockedProfilesAPIView(generics.ListAPIView):
    serializer_class = WalletSerializer
    permission_classes = [IsAdminOrSuperAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__phone_number', 'user__full_name', 'user__vendor_shop_profile__shop_name', 'user__business_profile__shop_name']

    def get_queryset(self):
        queryset = Wallet.objects.filter(
            Q(user__vendor_shop_profile__is_blocked=True) | 
            Q(user__business_profile__is_blocked=True)
        ).distinct().order_by('-created_at')

        profile_type = self.request.query_params.get('profile_type')
        if profile_type == 'vendor':
            queryset = queryset.filter(user__vendor_shop_profile__is_blocked=True)
        elif profile_type == 'service_provider':
            queryset = queryset.filter(user__business_profile__is_blocked=True)

        return queryset

    @swagger_auto_schema(
        tags=['Wallets'],
        operation_description="List all blocked profiles (vendors and service providers)",
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Search by phone, name, or shop name", type=openapi.TYPE_STRING),
            openapi.Parameter('profile_type', openapi.IN_QUERY, description="Filter by profile type", type=openapi.TYPE_STRING, enum=['vendor', 'service_provider']),
        ],
        responses={200: WalletSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)



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
    permission_classes = [IsAdminOrSuperAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['transaction_type']
    search_fields = ['description', 'wallet__user__phone_number', 'wallet__user__full_name']
