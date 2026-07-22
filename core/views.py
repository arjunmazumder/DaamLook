from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import ActiveUser, ActiveCustomer
from .serializers import UpdateLocationSerializer, UpdateCustomerLocationSerializer
from .utils import cleanup_inactive_locations
from drf_yasg.utils import swagger_auto_schema

class UpdateLocationView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Update User Location",
        operation_description="Updates the active location (latitude/longitude) of the currently authenticated user. Call this API every 5 minutes in the background.",
        request_body=UpdateLocationSerializer,
        responses={200: "Location updated successfully"}
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
        responses={200: "Customer location updated successfully"}
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
