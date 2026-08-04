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
from orders.models import VendorOrder, OrderCommission, ChatSessionInvoiceCommission
from services.models import ServiceBooking, ServiceProviderBusinessProfile, ServiceCommission
from vendors.models import ShopProfile
from .models import GlobalChatSession, GlobalChatMessage
from .admin_serializers import AdminGlobalChatSessionSerializer, AdminGlobalChatSessionDetailSerializer
from .serializers import GlobalChatMessageSerializer

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

        # Commission Calculation
        from django.utils import timezone
        today = timezone.now().date()
        this_month = today.month
        this_year = today.year

        def get_sum(qs):
            res = qs.aggregate(total=Sum('commission_amount'))['total']
            return float(res) if res else 0.0

        total_commission = get_sum(OrderCommission.objects.all()) + get_sum(ServiceCommission.objects.all()) + get_sum(ChatSessionInvoiceCommission.objects.all())
        
        daily_commission = get_sum(OrderCommission.objects.filter(created_at__date=today)) + \
                           get_sum(ServiceCommission.objects.filter(created_at__date=today)) + \
                           get_sum(ChatSessionInvoiceCommission.objects.filter(created_at__date=today))
                           
        monthly_commission = get_sum(OrderCommission.objects.filter(created_at__year=this_year, created_at__month=this_month)) + \
                             get_sum(ServiceCommission.objects.filter(created_at__year=this_year, created_at__month=this_month)) + \
                             get_sum(ChatSessionInvoiceCommission.objects.filter(created_at__year=this_year, created_at__month=this_month))

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
            ],
            "commissions": {
                "daily_commission": round(daily_commission, 2),
                "monthly_commission": round(monthly_commission, 2),
                "total_commission": round(total_commission, 2)
            }
        }
        
        return Response(data)

from django.utils.decorators import method_decorator

@method_decorator(name='list', decorator=swagger_auto_schema(
    tags=['Admin Panel'],
    operation_summary="List all chat sessions",
    manual_parameters=[
        openapi.Parameter('chat_type', openapi.IN_QUERY, description="Filter sessions by type: VENDOR or SERVICE", type=openapi.TYPE_STRING)
    ]
))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(
    tags=['Admin Panel'],
    operation_summary="Get chat session details and all messages"
))
class AdminGlobalChatSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Dedicated Admin API for viewing all chat sessions.
    """
    queryset = GlobalChatSession.objects.all().order_by('-updated_at')
    serializer_class = AdminGlobalChatSessionSerializer
    permission_classes = [IsAdminOrSuperAdmin]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AdminGlobalChatSessionDetailSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        qs = super().get_queryset()
        chat_type = self.request.query_params.get('chat_type')
        if chat_type:
            qs = qs.filter(chat_type=chat_type.upper())
        return qs

@method_decorator(name='list', decorator=swagger_auto_schema(
    tags=['Admin Panel'],
    operation_summary="List messages in chat sessions",
    manual_parameters=[
        openapi.Parameter('session_id', openapi.IN_QUERY, description="ID of the chat session to filter messages", type=openapi.TYPE_INTEGER)
    ]
))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(
    tags=['Admin Panel'],
    operation_summary="Get specific chat message details"
))
class AdminGlobalChatMessageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Dedicated Admin API for viewing messages in any chat session.
    """
    queryset = GlobalChatMessage.objects.all().order_by('-timestamp')
    serializer_class = GlobalChatMessageSerializer
    permission_classes = [IsAdminOrSuperAdmin]

    def get_queryset(self):
        qs = super().get_queryset()
        session_id = self.request.query_params.get('session_id')
        if session_id:
            qs = qs.filter(session_id=session_id)
        return qs
