from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from .permissions import IsAdminOrSuperAdmin
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth.models import Group, Permission
from .models import User
from .admin_serializers import AdminLoginSerializer, PermissionSerializer, RoleSerializer, StaffSerializer, StaffCreateSerializer
from .views import login_user, set_auth_cookies
from .serializers import UserWithProfileSerializer

class AdminLoginView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['Admin Panel'],
        operation_summary="Admin Staff Login",
        operation_description="Secure login endpoint specifically for Admin Panel Staff.",
        request_body=AdminLoginSerializer,
        responses={200: 'Login successful'}
    )
    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            access_token, refresh_token = login_user(user)
            
            response_data = {
                "status": "success",
                "message": "Admin login successful.",
                "data": {
                    "access_token": access_token,
                    "user": UserWithProfileSerializer(user).data
                }
            }
            
            response = Response(response_data, status=status.HTTP_200_OK)
            set_auth_cookies(response, access_token, refresh_token)
            return response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PermissionListView(ListAPIView):
    permission_classes = [IsAdminOrSuperAdmin]
    queryset = Permission.objects.all().order_by('content_type__app_label', 'codename')
    serializer_class = PermissionSerializer
    pagination_class = None

    @swagger_auto_schema(
        tags=['Admin Panel'],
        operation_summary="Get All Permissions",
        operation_description="List all available system permissions to assign to roles."
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class RoleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrSuperAdmin]
    queryset = Group.objects.all().order_by('name')
    serializer_class = RoleSerializer
    pagination_class = None

    @swagger_auto_schema(tags=['Admin Panel'], operation_summary="List all Roles")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Admin Panel'], operation_summary="Create a new Role (Group)")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Admin Panel'], operation_summary="Get Role details")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Admin Panel'], operation_summary="Update a Role")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Admin Panel'], operation_summary="Partially update a Role")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Admin Panel'], operation_summary="Delete a Role")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

class StaffViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrSuperAdmin]
    
    def get_queryset(self):
        return User.objects.filter(is_staff=True).prefetch_related('groups').order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return StaffCreateSerializer
        return StaffSerializer

    @swagger_auto_schema(tags=['Admin Panel'], operation_summary="List all Staff users")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Admin Panel'], operation_summary="Create a new Staff user")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Admin Panel'], operation_summary="Get Staff user details")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Admin Panel'], operation_summary="Update Staff user roles/details")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Admin Panel'], operation_summary="Partially update Staff user")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Admin Panel'], operation_summary="Delete a Staff user")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
