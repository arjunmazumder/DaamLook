from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ShopProfileViewSet, ShopReviewViewSet, CityViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'cities', CityViewSet, basename='city')
router.register(r'shops', ShopProfileViewSet, basename='vendor-shop')
router.register(r'reviews', ShopReviewViewSet, basename='vendor-review')


urlpatterns = [
    path('', include(router.urls)),
]
