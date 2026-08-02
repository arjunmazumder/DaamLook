from django.db.models import Q
from rest_framework import viewsets, permissions, exceptions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.decorators import method_decorator

from .models import Category, SubCategory, Product, BulkPricingTier, ProductImage
from .serializers import (
    CategorySerializer, SubCategorySerializer, 
    ProductSerializer, BulkPricingTierSerializer, ProductImageSerializer
)

from users.permissions import AdminBypassPermission

def is_admin(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    if hasattr(user, 'role') and user.role and user.role.name == 'ROLE' and user.role.value == 'ADMIN':
        return True
    return False

class IsAdminOrReadOnly(AdminBypassPermission):
    """
    Custom permission to only allow admins to edit objects.
    """
    def has_custom_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return False

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    # permission_classes = [IsAdminOrReadOnly]
    filter_backends = [SearchFilter]
    search_fields = ['name', 'description']

class SubCategoryViewSet(viewsets.ModelViewSet):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer
    # permission_classes = [IsAdminOrReadOnly]
    filter_backends = [SearchFilter]
    search_fields = ['name', 'description', 'category__name']


class IsVendorOrAdminOrReadOnly(AdminBypassPermission):
    def has_custom_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_custom_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Determine the shop related to the object
        shop = None
        if isinstance(obj, Product):
            shop = obj.shop
        elif hasattr(obj, 'product'):
            shop = obj.product.shop
            
        if shop and shop.user == request.user:
            return True
        return False

images_param = openapi.Parameter(
    'uploaded_images', 
    openapi.IN_FORM, 
    type=openapi.TYPE_ARRAY, 
    items=openapi.Items(type=openapi.TYPE_FILE), 
    description="Upload multiple images"
)

@method_decorator(name='create', decorator=swagger_auto_schema(manual_parameters=[images_param]))
@method_decorator(name='update', decorator=swagger_auto_schema(manual_parameters=[images_param]))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(manual_parameters=[images_param]))
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsVendorOrAdminOrReadOnly]
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ['title', 'description', 'size']
    filterset_fields = ['category', 'subcategory', 'product_type', 'shop', 'approval_status', 'size']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Product.objects.none()

        user = self.request.user

        if self.action == 'list':
            # Always return only APPROVED and active products for the main list endpoint
            return Product.objects.filter(approval_status='APPROVED', is_active=True, shop__is_blocked=False).order_by('-created_at')
            
        if is_admin(user):
            return Product.objects.all().order_by('-created_at')
            
        if user.is_authenticated:
            return Product.objects.filter(
                Q(approval_status='APPROVED', is_active=True, shop__is_blocked=False) |
                Q(shop__user=user)
            ).order_by('-created_at')

        return Product.objects.filter(approval_status='APPROVED', is_active=True, shop__is_blocked=False).order_by('-created_at')

    def perform_create(self, serializer):
        user = self.request.user
        if is_admin(user):
            product = serializer.save(approval_status='APPROVED')
        else:
            product = serializer.save(approval_status='PENDING')

        uploaded_images = self.request.FILES.getlist('uploaded_images')
        for image in uploaded_images:
            ProductImage.objects.create(product=product, image=image)

    def perform_update(self, serializer):
        product = serializer.save()
        uploaded_images = self.request.FILES.getlist('uploaded_images')
        for image in uploaded_images:
            ProductImage.objects.create(product=product, image=image)

    from users.permissions import IsAdminOrSuperAdmin
    @action(detail=False, methods=['get'], permission_classes=[IsAdminOrSuperAdmin])
    def pending(self, request):
        user = request.user
        if getattr(self, 'swagger_fake_view', False):
            return Response([])

        if is_admin(user):
            pending_products = Product.objects.filter(approval_status='PENDING')
        else:
            pending_products = Product.objects.filter(approval_status='PENDING', shop__user=user)

        page = self.paginate_queryset(pending_products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(pending_products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def rejected(self, request):
        user = request.user
        if getattr(self, 'swagger_fake_view', False):
            return Response([])

        if is_admin(user):
            rejected_products = Product.objects.filter(approval_status='REJECTED')
        else:
            rejected_products = Product.objects.filter(approval_status='REJECTED', shop__user=user)

        page = self.paginate_queryset(rejected_products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(rejected_products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def vendor(self, request):
        user = request.user
        if getattr(self, 'swagger_fake_view', False):
            return Response([])

        if is_admin(user):
            vendor_products = Product.objects.filter(approval_status='APPROVED', is_active=True)
        else:
            vendor_products = Product.objects.filter(approval_status='APPROVED', is_active=True, shop__user=user)

        page = self.paginate_queryset(vendor_products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(vendor_products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def search(self, request):
        query = request.query_params.get('search', '').strip()
        queryset = self.get_queryset() # This already filters for APPROVED and active products

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(shop__shop_name__icontains=query) |
                Q(category__name__icontains=query) |
                Q(subcategory__name__icontains=query)
            ).distinct()

        # Order by highest shop rating first
        queryset = queryset.order_by('-shop__average_rating', '-created_at')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BulkPricingTierViewSet(viewsets.ModelViewSet):
    queryset = BulkPricingTier.objects.all()
    serializer_class = BulkPricingTierSerializer
    permission_classes = [IsVendorOrAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product']

    def perform_create(self, serializer):
        product = serializer.validated_data.get('product')
        user = self.request.user
        if not is_admin(user):
            if product.shop.user != user:
                raise exceptions.PermissionDenied("You can only add pricing tiers to your own products.")
        serializer.save()


class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsVendorOrAdminOrReadOnly]
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product']

    def perform_create(self, serializer):
        product = serializer.validated_data.get('product')
        user = self.request.user
        if not is_admin(user):
            if product.shop.user != user:
                raise exceptions.PermissionDenied("You can only add images to your own products.")
        serializer.save()
