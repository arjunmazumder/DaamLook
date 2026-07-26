from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartViewSet, OrderViewSet, AdminOrderViewSet, VendorOrderViewSet

router = DefaultRouter()
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'buyer/orders', OrderViewSet, basename='buyer-orders')
router.register(r'admin/orders', AdminOrderViewSet, basename='admin-orders')
router.register(r'vendor/orders', VendorOrderViewSet, basename='vendor-orders')

urlpatterns = [
    path('', include(router.urls)),
]
