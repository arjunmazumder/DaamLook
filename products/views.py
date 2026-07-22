from django.db.models import Q
from rest_framework import viewsets, permissions, exceptions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import Category, SubCategory, Product, BulkPricingTier, ProductImage
from .serializers import (
    CategorySerializer, SubCategorySerializer, 
    ProductSerializer, BulkPricingTierSerializer, ProductImageSerializer
)

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit objects.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)

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


class IsVendorOrAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_staff or request.user.is_superuser:
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

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsVendorOrAdminOrReadOnly]
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ['title', 'description']
    filterset_fields = ['category', 'subcategory', 'product_type', 'shop', 'approval_status']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Product.objects.none()

        # Always return only APPROVED and active products for this endpoint
        return Product.objects.filter(approval_status='APPROVED', is_active=True)

    def perform_create(self, serializer):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            serializer.save(approval_status='APPROVED')
        else:
            serializer.save(approval_status='PENDING')

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def pending(self, request):
        user = request.user
        if getattr(self, 'swagger_fake_view', False):
            return Response([])

        if user.is_staff or user.is_superuser:
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

        if user.is_staff or user.is_superuser:
            rejected_products = Product.objects.filter(approval_status='REJECTED')
        else:
            rejected_products = Product.objects.filter(approval_status='REJECTED', shop__user=user)

        page = self.paginate_queryset(rejected_products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(rejected_products, many=True)
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
        if not (user.is_staff or user.is_superuser):
            if product.shop.user != user:
                raise exceptions.PermissionDenied("You can only add pricing tiers to your own products.")
        serializer.save()


class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsVendorOrAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product']

    def perform_create(self, serializer):
        product = serializer.validated_data.get('product')
        user = self.request.user
        if not (user.is_staff or user.is_superuser):
            if product.shop.user != user:
                raise exceptions.PermissionDenied("You can only add images to your own products.")
        serializer.save()
