from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth

from .models import BroadcastAnnouncement
from .admin_serializers import BroadcastAnnouncementSerializer
from users.permissions import IsAdminOrSuperAdmin
from users.models import User
from orders.models import VendorOrder
from services.models import ServiceBooking, ServiceProviderBusinessProfile
from vendors.models import ShopProfile

class BroadcastAnnouncementViewSet(viewsets.ModelViewSet):
    """
    Dedicated Admin API for creating and managing global announcements.
    """
    queryset = BroadcastAnnouncement.objects.all().order_by('-created_at')
    serializer_class = BroadcastAnnouncementSerializer
    permission_classes = [IsAdminOrSuperAdmin]

class AdminAnalyticsDashboardAPIView(APIView):
    """
    Returns aggregated stats for the Admin Dashboard.
    """
    permission_classes = [IsAdminOrSuperAdmin]

    @swagger_auto_schema(
        tags=['Admin Panel'],
        operation_summary="Get Analytics Dashboard Data",
        operation_description="Returns aggregated stats including user counts, sales volume trends, and top sellers."
    )
    def get(self, request, *args, **kwargs):
        total_users = User.objects.count()
        total_vendors = ShopProfile.objects.count()
        total_providers = ServiceProviderBusinessProfile.objects.count()

        total_product_orders = VendorOrder.objects.count()
        total_service_bookings = ServiceBooking.objects.count()

        # Product sales trend
        product_sales_trend = VendorOrder.objects.filter(status='DELIVERED') \
            .annotate(month=TruncMonth('created_at')) \
            .values('month') \
            .annotate(sales_volume=Sum('subtotal_amount')) \
            .order_by('month')

        # Service sales trend
        service_sales_trend = ServiceBooking.objects.filter(status='COMPLETED', payment_status='PAID') \
            .annotate(month=TruncMonth('created_at')) \
            .values('month') \
            .annotate(sales_volume=Sum('service_bill')) \
            .order_by('month')
            
        # Top Vendors (by average rating)
        top_vendors = ShopProfile.objects.order_by('-average_rating', '-total_reviews')[:5]
        top_providers = ServiceProviderBusinessProfile.objects.order_by('-average_rating', '-total_reviews')[:5]

        data = {
            "users": {
                "total": total_users,
                "vendors": total_vendors,
                "service_providers": total_providers
            },
            "orders": {
                "total_product_orders": total_product_orders,
                "total_service_bookings": total_service_bookings
            },
            "sales_trend": {
                "products": list(product_sales_trend),
                "services": list(service_sales_trend)
            },
            "top_vendors": [
                {"id": v.id, "shop_name": v.shop_name, "rating": v.average_rating} for v in top_vendors
            ],
            "top_service_providers": [
                {"id": p.id, "shop_name": p.shop_name, "rating": p.average_rating} for p in top_providers
            ]
        }
        
        return Response(data)
