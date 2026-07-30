from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from drf_yasg.utils import swagger_auto_schema
from .models import Wallet, WalletTransaction
from .serializers import WalletSerializer, WalletTransactionSerializer

class MyWalletView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['Wallets'], responses={200: WalletSerializer()})
    def get(self, request):
        """
        Get the current user's wallet details.
        """
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        serializer = WalletSerializer(wallet)
        return Response(serializer.data)

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from drf_yasg import openapi

class MyWalletTransactionsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WalletTransactionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['transaction_type']
    search_fields = ['description']

    @swagger_auto_schema(
        tags=['Wallets'], 
        operation_description="Get the current user's wallet transactions.",
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Search by transaction description", type=openapi.TYPE_STRING),
            openapi.Parameter('transaction_type', openapi.IN_QUERY, description="Filter by IN, OUT, or DISCOUNT", type=openapi.TYPE_STRING)
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        wallet, created = Wallet.objects.get_or_create(user=self.request.user)
        return WalletTransaction.objects.filter(wallet=wallet).order_by('-created_at')
