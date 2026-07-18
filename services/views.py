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

class FindNearbyProvidersView(APIView):
    permission_classes = [IsAdminOrSuperAdminOrBuyer]

    @swagger_auto_schema(
        operation_summary="Find Nearby Service Providers",
        operation_description="Find active service providers within 1km matching the buyer's desired category, updated within the last 5 mins.",
        responses={200: NearbyProviderSerializer(many=True)}
    )
    def get(self, request):
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

        # 4. Sort by distance
        nearby_providers.sort(key=lambda x: x['distance_km'])

        # 5. Serialize and return
        serializer = NearbyProviderSerializer(nearby_providers, many=True)
        return Response(serializer.data)
