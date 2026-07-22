from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceCategoryViewSet, ServiceProviderBusinessProfileViewSet, FindNearbyProvidersView, ChatViewSet, ServiceBookingViewSet, ServiceProviderReviewViewSet, ServiceInvoiceViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'categories', ServiceCategoryViewSet, basename='service-category')
router.register(r'business-profiles', ServiceProviderBusinessProfileViewSet, basename='business-profile')
router.register(r'chat', ChatViewSet, basename='chat')
router.register(r'bookings', ServiceBookingViewSet, basename='booking')
router.register(r'reviews', ServiceProviderReviewViewSet, basename='review')
router.register(r'invoices', ServiceInvoiceViewSet, basename='invoice')

urlpatterns = [
    path('nearby-providers/', FindNearbyProvidersView.as_view(), name='nearby-providers'),
    path('', include(router.urls)),
]
