from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartViewSet, OrderViewSet, AdminOrderViewSet, VendorOrderViewSet, DeliveryChargeViewSet, OrderCommissionViewSet

router = DefaultRouter()
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'buyer/orders', OrderViewSet, basename='buyer-orders')
router.register(r'admin/orders', AdminOrderViewSet, basename='admin-orders')
router.register(r'vendor/orders', VendorOrderViewSet, basename='vendor-orders')
router.register(r'delivery-charges', DeliveryChargeViewSet, basename='delivery-charges')
router.register(r'commissions', OrderCommissionViewSet, basename='order-commission')

urlpatterns = [
    path('', include(router.urls)),
]
