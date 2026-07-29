from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import ActiveUser, ActiveCustomer
from .serializers import UpdateLocationSerializer, UpdateCustomerLocationSerializer, UnifiedChatStartSerializer
from .utils import cleanup_inactive_locations
from services.models import ServiceProviderBusinessProfile, ChatSession
from vendors.models import ShopProfile, VendorChatSession
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class UpdateLocationView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Update User Location",
        operation_description="Updates the active location (latitude/longitude) of the currently authenticated user. Call this API every 5 minutes in the background.",
        request_body=UpdateLocationSerializer,
        responses={200: "Location updated successfully"},
        tags=['Core']
    )
    
    def post(self, request):
        # Auto-cleanup locations older than 5 minutes
        cleanup_inactive_locations(minutes=5)
        
        serializer = UpdateLocationSerializer(data=request.data)
        if serializer.is_valid():
            active_user, created = ActiveUser.objects.update_or_create(
                user=request.user,
                defaults={
                    'latitude': serializer.validated_data.get('latitude'),
                    'longitude': serializer.validated_data.get('longitude')
                }
            )
            return Response(
                {"message": "Location updated successfully", "data": serializer.data}, 
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateCustomerLocationView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Update Customer Location",
        operation_description="Updates the active location (latitude/longitude) and service category of the currently authenticated customer.",
        request_body=UpdateCustomerLocationSerializer,
        responses={200: "Customer location updated successfully"},
        tags=['Core']
    )
    def post(self, request):
        # Check if the user has a role and if it's a buyer
        if not request.user.role or request.user.role.name.lower() not in ['buyer', 'buyers']:
            return Response(
                {"error": "Permission denied. Only buyers can update their location here."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # Auto-cleanup locations older than 5 minutes
        cleanup_inactive_locations(minutes=5)

        serializer = UpdateCustomerLocationSerializer(data=request.data)
        if serializer.is_valid():
            active_customer, created = ActiveCustomer.objects.update_or_create(
                user=request.user,
                defaults={
                    'category': serializer.validated_data.get('category'),
                    'latitude': serializer.validated_data.get('latitude'),
                    'longitude': serializer.validated_data.get('longitude')
                }
            )
            return Response(
                {"message": "Customer location updated successfully", "data": serializer.data}, 
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Commission
from .serializers import CommissionSerializer
from django.utils.decorators import method_decorator

@method_decorator(name='list', decorator=swagger_auto_schema(tags=['Core']))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=['Core']))
@method_decorator(name='create', decorator=swagger_auto_schema(tags=['Core']))
@method_decorator(name='update', decorator=swagger_auto_schema(tags=['Core']))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(tags=['Core']))
@method_decorator(name='destroy', decorator=swagger_auto_schema(tags=['Core']))
class CommissionViewSet(viewsets.ModelViewSet):
    """
    CRUD API for Commissions.
    """
    queryset = Commission.objects.all().order_by('-created_at')
    serializer_class = CommissionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class UnifiedChatStartView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Unified Chat Start",
        operation_description="Start a chat with a Service Provider OR a Vendor. Pass `provider_id` to chat with a service provider, or `shop_id` to chat with a vendor.",
        request_body=UnifiedChatStartSerializer,
        responses={
            201: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'session_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='The ID of the Chat Session created'),
                    'chat_type': openapi.Schema(type=openapi.TYPE_STRING, description='"service" or "vendor"'),
                    'created': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='True if newly created')
                }
            )
        },
        tags=['Core Chat']
    )
    def post(self, request):
        provider_id = request.data.get('provider_id')
        shop_id = request.data.get('shop_id')

        if provider_id:
            try:
                provider = ServiceProviderBusinessProfile.objects.get(id=provider_id)
            except ServiceProviderBusinessProfile.DoesNotExist:
                return Response({"error": "Service Provider not found"}, status=status.HTTP_404_NOT_FOUND)

            if provider.provider == request.user:
                return Response({"error": "You cannot chat with yourself."}, status=status.HTTP_400_BAD_REQUEST)

            session, created = ChatSession.objects.get_or_create(
                buyer=request.user,
                provider=provider
            )
            return Response({"session_id": session.id, "chat_type": "service", "created": created}, status=status.HTTP_201_CREATED)

        elif shop_id:
            try:
                vendor = ShopProfile.objects.get(id=shop_id)
            except ShopProfile.DoesNotExist:
                return Response({"error": "Vendor not found"}, status=status.HTTP_404_NOT_FOUND)

            if vendor.user == request.user:
                return Response({"error": "You cannot chat with yourself."}, status=status.HTTP_400_BAD_REQUEST)

            session, created = VendorChatSession.objects.get_or_create(
                buyer=request.user,
                vendor=vendor
            )
            return Response({"session_id": session.id, "chat_type": "vendor", "created": created}, status=status.HTTP_201_CREATED)

        else:
            return Response({"error": "Either provider_id or shop_id is required."}, status=status.HTTP_400_BAD_REQUEST)
