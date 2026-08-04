from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import ServiceCategory
from .serializers import ServiceCategorySerializer

def is_admin(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    if hasattr(user, 'role') and user.role and user.role.name == 'ROLE' and user.role.value == 'ADMIN':
        return True
    return False

class ServiceCategoryViewSet(viewsets.ModelViewSet):
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    # permission_classes = [IsAuthenticatedOrReadOnly]

from .models import ServiceProviderBusinessProfile, Recentwork
from .serializers import ServiceProviderBusinessProfileSerializer, RecentworkSerializer
from users.permissions import IsAdminOrSuperAdminOrServiceProvider

from django_filters.rest_framework import DjangoFilterBackend

class ServiceProviderBusinessProfileViewSet(viewsets.ModelViewSet):
    queryset = ServiceProviderBusinessProfile.objects.all()
    serializer_class = ServiceProviderBusinessProfileSerializer
    # permission_classes = [IsAdminOrSuperAdminOrServiceProvider]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['categories']

    def get_queryset(self):
        if is_admin(self.request.user):
            return ServiceProviderBusinessProfile.objects.all()
        return ServiceProviderBusinessProfile.objects.filter(is_blocked=False)

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

class ProviderTotalEarnView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get Provider Total Earnings",
        operation_description="Returns total earnings, invoices, and bookings for the logged-in service provider."
    )
    def get(self, request):
        user = request.user
        
        # Admin checking admin stats is not applicable here as it requires no ID. 
        # This endpoint is specifically for the logged in provider.
        if not hasattr(user, 'business_profile'):
            return Response({"error": "You do not have a service provider profile."}, status=status.HTTP_403_FORBIDDEN)
            
        provider = user.business_profile
        
        # Total Bookings (Orders)
        total_bookings = provider.received_bookings.count()
        
        # Total Invoices
        from .models import ServiceInvoice
        invoices = ServiceInvoice.objects.filter(booking__provider=provider)
        total_invoices = invoices.count()
        
        # Total Earnings (sum of paid invoices)
        from django.db.models import Sum
        total_earnings = invoices.filter(payment_status='PAID').aggregate(Sum('total_amount'))['total_amount__sum'] or 0.0
        
        return Response({
            "provider_id": provider.id,
            "shop_name": provider.shop_name,
            "total_bookings": total_bookings,
            "total_invoices": total_invoices,
            "total_earnings": float(total_earnings)
        })

class RecentworkViewSet(viewsets.ModelViewSet):
    queryset = Recentwork.objects.all()
    serializer_class = RecentworkSerializer
    permission_classes = [IsAdminOrSuperAdminOrServiceProvider]

    def get_queryset(self):
        if is_admin(self.request.user):
            return Recentwork.objects.all()
        return Recentwork.objects.filter(provider__is_blocked=False)

from rest_framework.views import APIView
from rest_framework.response import Response
from users.permissions import IsAdminOrSuperAdminOrBuyer
from django.utils import timezone
from datetime import timedelta
from core.models import ActiveUser, ActiveCustomer
from .serializers import NearbyProviderSerializer
from .utils import calculate_distance
from drf_yasg.utils import swagger_auto_schema

from core.utils import cleanup_inactive_locations

class FindNearbyProvidersView(APIView):
    # permission_classes = [IsAdminOrSuperAdminOrBuyer]

    @swagger_auto_schema(
        operation_summary="Find Nearby Service Providers",
        operation_description="Find active service providers within 1km matching the buyer's desired category, updated within the last 5 mins.",
        responses={200: NearbyProviderSerializer(many=True)}
    )
    def get(self, request):
        # Auto-cleanup locations older than 5 minutes
        cleanup_inactive_locations(minutes=5)

        try:
            active_customer = request.user.active_customer_location
        except ActiveCustomer.DoesNotExist:
            return Response({"error": "No location found for this buyer. Please update your location first."}, status=400)
            
        buyer_lat = active_customer.latitude
        buyer_lon = active_customer.longitude
        desired_category = active_customer.category
        
        if not buyer_lat or not buyer_lon or not desired_category:
            return Response({"error": "Missing location or category information."}, status=400)

        # 2. Filter ActiveUser (Providers) updated within last 5 minutes
        five_mins_ago = timezone.now() - timedelta(minutes=5)
        recent_active_users = ActiveUser.objects.filter(
            updated_at__gte=five_mins_ago,
            latitude__isnull=False,
            longitude__isnull=False,
            user__business_profile__categories=desired_category,
            user__business_profile__is_blocked=False
        ).select_related('user__business_profile')

        # 3. Calculate distance and filter by 1km
        nearby_providers = []
        for active_user in recent_active_users:
            try:
                business_profile = active_user.user.business_profile
            except ServiceProviderBusinessProfile.DoesNotExist:
                continue
                
            dist = calculate_distance(
                buyer_lat, buyer_lon, 
                active_user.latitude, active_user.longitude
            )
            
            if dist <= 1.0:
                nearby_providers.append({
                    'provider_id': active_user.user.id,
                    'shop_name': business_profile.shop_name,
                    'contact_number': business_profile.contact_number,
                    'address': business_profile.address,
                    'average_rating': business_profile.average_rating,
                    'total_reviews': business_profile.total_reviews,
                    'distance_km': round(dist, 2),
                    'latitude': active_user.latitude,
                    'longitude': active_user.longitude
                })

        # 4. Sort by highest average rating first, then by closest distance
        nearby_providers.sort(key=lambda x: (-x['average_rating'], x['distance_km']))

        # 5. Serialize and return
        serializer = NearbyProviderSerializer(nearby_providers, many=True)
        return Response(serializer.data)

from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .models import ServiceBooking, ServiceProviderNotification, ServiceProviderReview
from .serializers import ServiceBookingSerializer, ServiceProviderReviewSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models import Q



from django.utils.decorators import method_decorator

status_param = openapi.Parameter('status', openapi.IN_QUERY, description="Filter by booking status (e.g. PENDING, CONFIRMED, COMPLETED)", type=openapi.TYPE_STRING)
payment_status_param = openapi.Parameter('payment_status', openapi.IN_QUERY, description="Filter by payment status (e.g. UNPAID, PAID)", type=openapi.TYPE_STRING)
category_param = openapi.Parameter('category', openapi.IN_QUERY, description="Filter by service category ID", type=openapi.TYPE_INTEGER)
scheduled_date_param = openapi.Parameter('scheduled_date', openapi.IN_QUERY, description="Filter by scheduled date (YYYY-MM-DD)", type=openapi.TYPE_STRING)

@method_decorator(name='list', decorator=swagger_auto_schema(
    tags=['services'],
    operation_summary="List Service Bookings",
    manual_parameters=[status_param, payment_status_param, category_param, scheduled_date_param]
))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=['services']))
@method_decorator(name='create', decorator=swagger_auto_schema(tags=['services']))
@method_decorator(name='update', decorator=swagger_auto_schema(tags=['services']))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(tags=['services']))
@method_decorator(name='destroy', decorator=swagger_auto_schema(tags=['services']))
class ServiceBookingViewSet(viewsets.ModelViewSet):
    queryset = ServiceBooking.objects.all()
    serializer_class = ServiceBookingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'payment_status', 'category', 'scheduled_date']


    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ServiceBooking.objects.none()

        user = self.request.user
        if not user.is_authenticated:
            return ServiceBooking.objects.none()

        # Users can only see their own bookings (as buyer or provider)
        if hasattr(user, 'business_profile'):
            return ServiceBooking.objects.filter(Q(buyer=user) | Q(provider=user.business_profile))
        return ServiceBooking.objects.filter(buyer=user)

    def perform_create(self, serializer):
        # Create the booking
        booking = serializer.save()

        # Create a notification for the provider
        try:
            provider_user = booking.provider.provider
            category_name = booking.category.name if booking.category else "a service"
            notification = ServiceProviderNotification.objects.create(
                provider=provider_user,
                booking=booking,
                message=f"You have a new booking request for {category_name}."
            )

            # Push notification via WebSockets
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'notifications_{provider_user.id}',
                {
                    'type': 'notification_message',
                    'notification_id': notification.id,
                    'message': notification.message,
                    'booking_id': booking.id
                }
            )
        except Exception as e:
            # Handle error gracefully so it doesn't fail booking creation
            print("Failed to send notification:", e)

    @action(detail=True, methods=['patch'])
    def confirm(self, request, pk=None):
        booking = self.get_object()
        
        # Verify the user is the provider for this booking
        if not hasattr(request.user, 'business_profile') or booking.provider != request.user.business_profile:
            return Response({"error": "Only the assigned provider can confirm this booking."}, status=403)
            
        if booking.status != 'PENDING':
            return Response({"error": f"Cannot confirm a booking with status: {booking.status}"}, status=400)
            
        booking.status = 'CONFIRMED'
        booking.save()
        return Response(self.get_serializer(booking).data)

    @action(detail=True, methods=['patch'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        
        # Verify the user is the provider for this booking
        if not hasattr(request.user, 'business_profile') or booking.provider != request.user.business_profile:
            return Response({"error": "Only the assigned provider can cancel this booking."}, status=403)
            
        if booking.status in ['COMPLETED', 'CANCELLED']:
            return Response({"error": f"Cannot cancel a booking with status: {booking.status}"}, status=400)
            
        cancellation_reason = request.data.get('cancellation_reason', 'Cancelled by provider.')
        booking.status = 'CANCELLED'
        booking.cancellation_reason = cancellation_reason
        booking.save()
        return Response(self.get_serializer(booking).data)

from rest_framework import exceptions
from django.db.models import Avg

class ServiceProviderReviewViewSet(viewsets.ModelViewSet):
    queryset = ServiceProviderReview.objects.all()
    serializer_class = ServiceProviderReviewSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        booking = serializer.validated_data.get('booking')
        
        if booking.buyer != self.request.user:
            raise exceptions.PermissionDenied("You can only review your own bookings.")
            
        if booking.status != 'COMPLETED':
            raise exceptions.ValidationError({"error": "You can only review a completed booking."})

        # Save review
        review = serializer.save(
            reviewer=self.request.user,
            reviewee=booking.provider
        )

        # Update provider's overall rating
        provider = booking.provider
        reviews = ServiceProviderReview.objects.filter(reviewee=provider)
        
        total = reviews.count()
        avg_rating = reviews.aggregate(Avg('rating_stars'))['rating_stars__avg'] or 0.0
        
        provider.total_reviews = total
        provider.average_rating = round(avg_rating, 2)
        provider.save()

from .models import ServiceInvoice
from .serializers import ServiceInvoiceSerializer

class ServiceInvoiceViewSet(viewsets.ModelViewSet):
    queryset = ServiceInvoice.objects.all()
    serializer_class = ServiceInvoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ServiceInvoice.objects.none()

        user = self.request.user
        if not user.is_authenticated:
            return ServiceInvoice.objects.none()

        if is_admin(user):
            return ServiceInvoice.objects.all()
            
        if hasattr(user, 'business_profile'):
            return ServiceInvoice.objects.filter(
                Q(booking__buyer=user) | Q(booking__provider=user.business_profile)
            )
        return ServiceInvoice.objects.filter(booking__buyer=user)

    def perform_create(self, serializer):
        booking = serializer.validated_data.get('booking')
        user = self.request.user

        if not is_admin(user):
            if not hasattr(user, 'business_profile') or booking.provider != user.business_profile:
                raise exceptions.PermissionDenied("Only the assigned service provider can create an invoice for this booking.")

        serializer.save()

    def perform_update(self, serializer):
        invoice = self.get_object()
        user = self.request.user

        is_buyer = (invoice.booking.buyer == user)
        is_provider = (hasattr(user, 'business_profile') and invoice.booking.provider == user.business_profile)
        if not (is_buyer or is_provider or is_admin(user)):
            raise exceptions.PermissionDenied("You are not authorized to update this invoice.")

        serializer.save()

    @action(detail=True, methods=['patch'], url_path='pay')
    def pay(self, request, pk=None):
        invoice = self.get_object()
        user = request.user
        if invoice.booking.buyer != user and not is_admin(user):
            return Response({"error": "Only the buyer can pay this invoice."}, status=403)

        if invoice.payment_status == 'PAID':
            return Response({"error": "Invoice is already paid."}, status=400)

        payment_method = request.data.get('payment_method')
        transaction_id = request.data.get('transaction_id', '')

        if not payment_method:
            return Response({"error": "payment_method is required."}, status=400)

        invoice.payment_method = payment_method
        invoice.transaction_id = transaction_id
        invoice.payment_status = 'PAID'
        invoice.save()

        return Response(self.get_serializer(invoice).data)

from .models import ServiceCommission
from .serializers import ServiceCommissionSerializer

class ServiceCommissionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ServiceCommissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ServiceCommission.objects.none()

        user = self.request.user
        if not user.is_authenticated:
            return ServiceCommission.objects.none()

        if is_admin(user):
            return ServiceCommission.objects.all().order_by('-created_at')
            
        if hasattr(user, 'business_profile'):
            return ServiceCommission.objects.filter(
                invoice__booking__provider=user.business_profile
            ).order_by('-created_at')
            
        return ServiceCommission.objects.none()
