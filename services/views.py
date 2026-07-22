from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import ServiceCategory
from .serializers import ServiceCategorySerializer

class ServiceCategoryViewSet(viewsets.ModelViewSet):
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

from .models import ServiceProviderBusinessProfile
from .serializers import ServiceProviderBusinessProfileSerializer
from users.permissions import IsAdminOrSuperAdminOrServiceProvider

class ServiceProviderBusinessProfileViewSet(viewsets.ModelViewSet):
    queryset = ServiceProviderBusinessProfile.objects.all()
    serializer_class = ServiceProviderBusinessProfileSerializer
    permission_classes = [IsAdminOrSuperAdminOrServiceProvider]

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
    permission_classes = [IsAdminOrSuperAdminOrBuyer]

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
            user__business_profile__categories=desired_category
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
from .models import ChatSession, ChatMessage, ServiceBooking, ServiceProviderNotification, ServiceProviderReview
from .serializers import ChatSessionSerializer, ChatMessageSerializer, ServiceBookingSerializer, ServiceProviderReviewSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models import Q

class ChatViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def start(self, request):
        provider_id = request.data.get('provider_id')
        if not provider_id:
            return Response({"error": "provider_id is required"}, status=400)
        
        try:
            provider = ServiceProviderBusinessProfile.objects.get(id=provider_id)
        except ServiceProviderBusinessProfile.DoesNotExist:
            return Response({"error": "Provider not found"}, status=404)

        session, created = ChatSession.objects.get_or_create(
            buyer=request.user,
            provider=provider
        )
        return Response({"session_id": session.id, "created": created})

    @action(detail=False, methods=['get'])
    def inbox(self, request):
        user = request.user
        sessions = ChatSession.objects.filter(
            Q(buyer=user) | Q(provider__provider=user)
        ).order_by('-updated_at')
        
        serializer = ChatSessionSerializer(sessions, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        try:
            session = ChatSession.objects.get(id=pk)
        except ChatSession.DoesNotExist:
            return Response({"error": "Session not found"}, status=404)
        
        # Verify participant
        is_buyer = (session.buyer == request.user)
        is_provider = False
        if hasattr(request.user, 'business_profile') and session.provider == request.user.business_profile:
            is_provider = True

        if not is_buyer and not is_provider:
            return Response({"error": "Unauthorized"}, status=403)
            
        # Mark unread messages as read
        unread_messages = session.messages.filter(is_read=False).exclude(sender=request.user)
        unread_messages.update(is_read=True)

        messages = session.messages.all()
        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='create-invoice')
    def create_invoice(self, request, pk=None):
        try:
            session = ChatSession.objects.get(id=pk)
        except ChatSession.DoesNotExist:
            return Response({"error": "Session not found"}, status=404)
            
        data = request.data.copy()
        data['chat_session'] = session.id
        data['buyer'] = session.buyer.id
        data['provider'] = session.provider.id
        
        serializer = ServiceBookingSerializer(data=data)
        if serializer.is_valid():
            booking = serializer.save()
            
            # Create a system message for the invoice
            msg = ChatMessage.objects.create(
                session=session,
                sender=request.user,
                message_type='INVOICE',
                message=f"Invoice created: {booking.service_number}"
            )
            
            # Push via channels
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{session.id}',
                {
                    'type': 'chat_message',
                    'id': msg.id,
                    'message': msg.message,
                    'message_type': msg.message_type,
                    'sender_id': request.user.id,
                    'timestamp': str(msg.timestamp)
                }
            )
            
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class ServiceBookingViewSet(viewsets.ModelViewSet):
    queryset = ServiceBooking.objects.all()
    serializer_class = ServiceBookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can only see their own bookings (as buyer or provider)
        user = self.request.user
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

        if user.is_staff or user.is_superuser:
            return ServiceInvoice.objects.all()
            
        if hasattr(user, 'business_profile'):
            return ServiceInvoice.objects.filter(
                Q(booking__buyer=user) | Q(booking__provider=user.business_profile)
            )
        return ServiceInvoice.objects.filter(booking__buyer=user)

    def perform_create(self, serializer):
        booking = serializer.validated_data.get('booking')
        user = self.request.user

        if not (user.is_staff or user.is_superuser):
            if not hasattr(user, 'business_profile') or booking.provider != user.business_profile:
                raise exceptions.PermissionDenied("Only the assigned service provider can create an invoice for this booking.")

        serializer.save()

    def perform_update(self, serializer):
        invoice = self.get_object()
        user = self.request.user

        is_buyer = (invoice.booking.buyer == user)
        is_provider = (hasattr(user, 'business_profile') and invoice.booking.provider == user.business_profile)
        is_admin = user.is_staff or user.is_superuser

        if not (is_buyer or is_provider or is_admin):
            raise exceptions.PermissionDenied("You are not authorized to update this invoice.")

        serializer.save()

    @action(detail=True, methods=['patch'], url_path='pay')
    def pay(self, request, pk=None):
        invoice = self.get_object()
        if invoice.booking.buyer != request.user and not (request.user.is_staff or request.user.is_superuser):
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
