from rest_framework import viewsets, exceptions, status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import ShopProfile, ShopReview
from .serializers import ShopProfileSerializer, ShopReviewSerializer

class ShopProfileViewSet(viewsets.ModelViewSet):
    queryset = ShopProfile.objects.all()
    serializer_class = ShopProfileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = ShopProfile.objects.all()
        shop_type = self.request.query_params.get('shop_type')
        search = self.request.query_params.get('search')

        if shop_type:
            queryset = queryset.filter(shop_type=shop_type.upper())
        if search:
            queryset = queryset.filter(Q(shop_name__icontains=search) | Q(description__icontains=search))
            
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if ShopProfile.objects.filter(user=user).exists():
            raise exceptions.ValidationError({"error": "You already have a shop profile."})
        serializer.save(user=user)

    def perform_update(self, serializer):
        shop = self.get_object()
        user = self.request.user
        if shop.user != user and not (user.is_staff or user.is_superuser):
            raise exceptions.PermissionDenied("You can only edit your own shop profile.")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if instance.user != user and not (user.is_staff or user.is_superuser):
            raise exceptions.PermissionDenied("You can only delete your own shop profile.")
        instance.delete()

    @action(detail=False, methods=['get', 'put', 'patch'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        GET /api/vendors/shops/me - Retrieve logged-in vendor's shop profile.
        PUT/PATCH /api/vendors/shops/me - Update logged-in vendor's shop profile.
        """
        try:
            shop = request.user.vendor_shop_profile
        except ShopProfile.DoesNotExist:
            return Response({"error": "Shop profile not found for this user."}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            serializer = self.get_serializer(shop)
            return Response(serializer.data)

        serializer = self.get_serializer(shop, data=request.data, partial=(request.method == 'PATCH'))
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShopReviewViewSet(viewsets.ModelViewSet):
    queryset = ShopReview.objects.all()
    serializer_class = ShopReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = ShopReview.objects.all()
        shop_id = self.request.query_params.get('shop')
        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        return queryset

    def perform_create(self, serializer):
        shop = serializer.validated_data.get('shop')
        user = self.request.user

        if shop.user == user:
            raise exceptions.PermissionDenied("You cannot review your own shop.")

        # Update if user already reviewed this shop, or save new
        existing_review = ShopReview.objects.filter(shop=shop, reviewer=user).first()
        if existing_review:
            for key, value in serializer.validated_data.items():
                setattr(existing_review, key, value)
            existing_review.save()
        else:
            serializer.save(reviewer=user)

    def perform_update(self, serializer):
        review = self.get_object()
        user = self.request.user
        if review.reviewer != user and not (user.is_staff or user.is_superuser):
            raise exceptions.PermissionDenied("You can only edit your own review.")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if instance.reviewer != user and not (user.is_staff or user.is_superuser):
            raise exceptions.PermissionDenied("You can only delete your own review.")
        instance.delete()
