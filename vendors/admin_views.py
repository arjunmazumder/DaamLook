from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import ShopProfile
from .serializers import ShopProfileSerializer
from users.permissions import IsAdminOrSuperAdmin

class AdminVendorRatingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Dedicated Admin API for monitoring and adjusting Vendor Ratings.
    """
    queryset = ShopProfile.objects.all().order_by('-average_rating')
    serializer_class = ShopProfileSerializer
    permission_classes = [IsAdminOrSuperAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    
    # Enable filtering by shop type
    filterset_fields = ['shop_type']
    # Enable text search by shop name or phone number
    search_fields = ['shop_name', 'user__phone_number', 'contact_email']

    @swagger_auto_schema(
        tags=['Admin Panel'],
        operation_summary="List all Vendors with Ratings",
        operation_description="Fetch all vendors to monitor their ratings and review counts."
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Admin Panel'],
        operation_summary="Get specific Vendor Rating details"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Admin Panel'],
        operation_summary="Adjust Vendor Rating",
        operation_description="Admin can manually adjust the rating of a vendor by providing an adjustment value (e.g. +1.0 or -0.5).",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['admin_rating_adjustment'],
            properties={
                'admin_rating_adjustment': openapi.Schema(type=openapi.TYPE_NUMBER, description='Adjustment value to add/subtract from the real average rating'),
            }
        ),
        responses={200: ShopProfileSerializer()}
    )
    @action(detail=True, methods=['patch'])
    def adjust_rating(self, request, pk=None):
        shop = self.get_object()
        adjustment = request.data.get('admin_rating_adjustment')
        
        if adjustment is None:
            return Response({"error": "admin_rating_adjustment is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            adjustment = float(adjustment)
        except ValueError:
            return Response({"error": "Invalid adjustment value. Must be a number."}, status=status.HTTP_400_BAD_REQUEST)
            
        shop.admin_rating_adjustment = adjustment
        # Trigger the recalculation
        
        # Calculate base average from reviews
        reviews = shop.reviews.all()
        total = reviews.count()
        if total > 0:
            avg = sum(r.average_rating for r in reviews) / float(total)
        else:
            avg = 0.0
            
        shop.average_rating = min(max(round(avg + shop.admin_rating_adjustment, 2), 0.0), 5.0)
        shop.save(update_fields=['admin_rating_adjustment', 'average_rating', 'updated_at'])
        
        return Response(self.get_serializer(shop).data)


