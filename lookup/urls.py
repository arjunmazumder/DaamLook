from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LookupViewSet

router = DefaultRouter()
router.register(r'items', LookupViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
