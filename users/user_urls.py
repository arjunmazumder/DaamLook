from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import KYCProfileView, UserViewSet, ShippingAddressView

router = SimpleRouter(trailing_slash=False)
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    path('profile/', KYCProfileView.as_view(), name='user-profile'),
    path('shipping-address/', ShippingAddressView.as_view(), name='shipping-address'),
    path('', include(router.urls)),
]
