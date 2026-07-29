from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UpdateLocationView, UpdateCustomerLocationView, CommissionViewSet, UnifiedChatStartView

router = DefaultRouter(trailing_slash=False)
router.register(r'commissions', CommissionViewSet, basename='commission')

urlpatterns = [
    path('update-location/', UpdateLocationView.as_view(), name='update-location'),
    path('update-customer-location/', UpdateCustomerLocationView.as_view(), name='update-customer-location'),
    path('chat/start/', UnifiedChatStartView.as_view(), name='unified-chat-start'),
    path('', include(router.urls)),
]
