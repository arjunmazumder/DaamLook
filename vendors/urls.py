from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ShopProfileViewSet, ShopReviewViewSet, VendorChatSessionViewSet, VendorChatMessageViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'shops', ShopProfileViewSet, basename='vendor-shop')
router.register(r'reviews', ShopReviewViewSet, basename='vendor-review')
router.register(r'chats/sessions', VendorChatSessionViewSet, basename='vendor-chat-session')
router.register(r'chats/messages', VendorChatMessageViewSet, basename='vendor-chat-message')

urlpatterns = [
    path('', include(router.urls)),
]
