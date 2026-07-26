from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import VendorOrder
from .serializers import VendorOrderSerializer
from users.permissions import IsAdminOrSuperAdmin

class AdminProductOrderMonitoringViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Dedicated Admin API for monitoring and overriding Product Orders (VendorOrders).
    """
    queryset = VendorOrder.objects.all().order_by('-created_at')
    serializer_class = VendorOrderSerializer
    permission_classes = [IsAdminOrSuperAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    
    # Enable filtering by status and specific vendor
    filterset_fields = ['status', 'vendor_shop']
    # Enable text search by vendor shop name or order number
    search_fields = ['vendor_shop__shop_name', 'vendor_order_number']

    @swagger_auto_schema(
        tags=['Admin Panel'],
        operation_summary="List all Product Orders (Vendor Orders)",
        operation_description="Fetch all vendor orders for admin monitoring."
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Admin Panel'],
        operation_summary="Get specific Product Order details"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Admin Panel'],
        operation_summary="Override Order Status",
        operation_description="Admin can manually update the status of any order (e.g. Cancel a stuck order).",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['status'],
            properties={
                'status': openapi.Schema(type=openapi.TYPE_STRING, description='New status (PROCESSING, PACKED, SHIPPED, DELIVERED, CANCELLED)'),
            }
        ),
        responses={200: VendorOrderSerializer()}
    )
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        vendor_order = self.get_object()
        new_status = request.data.get('status')
        
        valid_statuses = [c[0] for c in VendorOrder.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)
            
        vendor_order.status = new_status
        vendor_order.save()
        
        return Response(self.get_serializer(vendor_order).data)
