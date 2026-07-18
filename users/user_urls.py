from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import KYCProfileView, UserViewSet

router = SimpleRouter(trailing_slash=False)
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    path('profile/', KYCProfileView.as_view(), name='user-profile'),
    path('', include(router.urls)),
]
