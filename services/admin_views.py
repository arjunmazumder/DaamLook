from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import ServiceBooking, ServiceProviderBusinessProfile
from .serializers import ServiceBookingSerializer, ServiceProviderBusinessProfileSerializer
from users.permissions import IsAdminOrSuperAdmin

class AdminServiceBookingMonitoringViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Dedicated Admin API for monitoring and overriding Service Bookings.
    """
    queryset = ServiceBooking.objects.all().order_by('-created_at')
    serializer_class = ServiceBookingSerializer
    permission_classes = [IsAdminOrSuperAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    
    # Enable filtering by status, provider
    filterset_fields = ['status', 'provider']
    # Enable text search by provider shop name or service number
    search_fields = ['provider__shop_name', 'service_number', 'buyer__phone_number']

    @swagger_auto_schema(
        tags=['Admin Panel'],
        operation_summary="List all Service Bookings",
        operation_description="Fetch all service bookings for admin monitoring."
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Admin Panel'],
        operation_summary="Get specific Service Booking details"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Admin Panel'],
        operation_summary="Override Booking Status",
        operation_description="Admin can manually update the status of any booking (e.g. Cancel a problematic booking).",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['status'],
            properties={
                'status': openapi.Schema(type=openapi.TYPE_STRING, description='New status (PENDING, CONFIRMED, COMPLETED, CANCELLED)'),
                'cancellation_reason': openapi.Schema(type=openapi.TYPE_STRING, description='Reason if cancelling'),
            }
        ),
        responses={200: ServiceBookingSerializer()}
    )
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        booking = self.get_object()
        new_status = request.data.get('status')
        
        valid_statuses = [c[0] for c in ServiceBooking.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)
            
        booking.status = new_status
        if new_status == 'CANCELLED':
            booking.cancellation_reason = request.data.get('cancellation_reason', 'Cancelled by Admin')
            
        booking.save()
        
        return Response(self.get_serializer(booking).data)

class AdminProviderRatingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Dedicated Admin API for monitoring and adjusting Service Provider Ratings.
    """
    queryset = ServiceProviderBusinessProfile.objects.all().order_by('-average_rating')
    serializer_class = ServiceProviderBusinessProfileSerializer
    permission_classes = [IsAdminOrSuperAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    
    # Enable filtering by category
    filterset_fields = ['categories']
    # Enable text search by shop name or contact number
    search_fields = ['shop_name', 'contact_number', 'provider__phone_number']

    @swagger_auto_schema(
        tags=['Admin Panel'],
        operation_summary="List all Service Providers with Ratings"
    )
    def list(self, request, *args, **kwargs):
        # Workaround for empty categories filter causing 400 Bad Request
        if 'categories' in request.query_params and request.query_params['categories'] == '':
            request.query_params._mutable = True
            request.query_params.pop('categories')
            request.query_params._mutable = False
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Admin Panel'],
        operation_summary="Get specific Service Provider Rating details"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Admin Panel'],
        operation_summary="Adjust Provider Rating",
        operation_description="Admin can manually adjust the rating of a provider by providing an adjustment value (e.g. +1.0 or -0.5).",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['admin_rating_adjustment'],
            properties={
                'admin_rating_adjustment': openapi.Schema(type=openapi.TYPE_NUMBER, description='Adjustment value to add/subtract from the real average rating'),
            }
        ),
        responses={200: ServiceProviderBusinessProfileSerializer()}
    )
    @action(detail=True, methods=['patch'])
    def adjust_rating(self, request, pk=None):
        provider = self.get_object()
        adjustment = request.data.get('admin_rating_adjustment')
        
        if adjustment is None:
            return Response({"error": "admin_rating_adjustment is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            adjustment = float(adjustment)
        except ValueError:
            return Response({"error": "Invalid adjustment value. Must be a number."}, status=status.HTTP_400_BAD_REQUEST)
            
        provider.admin_rating_adjustment = adjustment
        
        # Calculate base average from reviews
        reviews = provider.received_reviews.all()
        total = reviews.count()
        if total > 0:
            avg = sum(r.rating_stars for r in reviews) / float(total)
        else:
            avg = 0.0
            
        provider.average_rating = min(max(round(avg + provider.admin_rating_adjustment, 2), 0.0), 5.0)
        provider.save(update_fields=['admin_rating_adjustment', 'average_rating', 'updated_at'])
        
        return Response(self.get_serializer(provider).data)
    

