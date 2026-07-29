from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .admin_views import AdminLoginView, PermissionListView, RoleViewSet, StaffViewSet
from orders.admin_views import AdminProductOrderMonitoringViewSet
from services.admin_views import AdminServiceBookingMonitoringViewSet, AdminProviderRatingViewSet
from vendors.admin_views import AdminVendorRatingViewSet
from core.admin_views import AdminAnalyticsDashboardAPIView, BroadcastAnnouncementViewSet

router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='admin-roles')
router.register(r'staff', StaffViewSet, basename='admin-staff')
router.register(r'monitoring/product-orders', AdminProductOrderMonitoringViewSet, basename='admin-monitoring-products')
router.register(r'monitoring/service-bookings', AdminServiceBookingMonitoringViewSet, basename='admin-monitoring-services')
router.register(r'ratings/vendors', AdminVendorRatingViewSet, basename='admin-ratings-vendors')
router.register(r'ratings/service-providers', AdminProviderRatingViewSet, basename='admin-ratings-providers')

router.register(r'broadcast', BroadcastAnnouncementViewSet, basename='admin-broadcast')

urlpatterns = [
    path('login/', AdminLoginView.as_view(), name='admin-login'),
    path('permissions/', PermissionListView.as_view(), name='admin-permissions'),
    path('dashboard/analytics/', AdminAnalyticsDashboardAPIView.as_view(), name='admin-analytics'),
    path('', include(router.urls)),
]
