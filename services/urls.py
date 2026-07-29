from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceCategoryViewSet, ServiceProviderBusinessProfileViewSet, FindNearbyProvidersView, ServiceBookingViewSet, ServiceProviderReviewViewSet, ServiceInvoiceViewSet, ServiceCommissionViewSet, RecentworkViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'categories', ServiceCategoryViewSet, basename='service-category')
router.register(r'business-profiles', ServiceProviderBusinessProfileViewSet, basename='business-profile')
router.register(r'bookings', ServiceBookingViewSet, basename='booking')
router.register(r'reviews', ServiceProviderReviewViewSet, basename='review')
router.register(r'invoices', ServiceInvoiceViewSet, basename='invoice')
router.register(r'commissions', ServiceCommissionViewSet, basename='service-commission')
router.register(r'recent-works', RecentworkViewSet, basename='recent-work')

urlpatterns = [
    path('nearby-providers/', FindNearbyProvidersView.as_view(), name='nearby-providers'),
    path('', include(router.urls)),
]
