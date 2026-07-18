from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceCategoryViewSet, ServiceProviderBusinessProfileViewSet, FindNearbyProvidersView

router = DefaultRouter(trailing_slash=False)
router.register(r'categories', ServiceCategoryViewSet, basename='service-category')
router.register(r'business-profiles', ServiceProviderBusinessProfileViewSet, basename='business-profile')

urlpatterns = [
    path('nearby-providers/', FindNearbyProvidersView.as_view(), name='nearby-providers'),
    path('', include(router.urls)),
]
