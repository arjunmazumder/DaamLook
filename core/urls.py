from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UpdateLocationView, UpdateCustomerLocationView, CommissionViewSet, GlobalChatSessionViewSet, GlobalChatMessageViewSet, InboxContactsView, ChatSessionInvoiceViewSet, ChatSessionInvoiceCommissionViewSet, AllCategoriesView, PolicyViewSet, AboutUsViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'commissions', CommissionViewSet, basename='commission')
router.register(r'chats/sessions', GlobalChatSessionViewSet, basename='global-chat-session')
router.register(r'chats/messages', GlobalChatMessageViewSet, basename='global-chat-message')
router.register(r'chats/invoices', ChatSessionInvoiceViewSet, basename='chat-invoice')
router.register(r'chats/commissions', ChatSessionInvoiceCommissionViewSet, basename='chat-commission')
router.register(r'policies', PolicyViewSet, basename='policy')

router.register(r"about-us", AboutUsViewSet, basename="about-us")

urlpatterns = [
    path('all-categories/', AllCategoriesView.as_view(), name='all-categories'),
    path('update-location/', UpdateLocationView.as_view(), name='update-location'),
    path('update-customer-location/', UpdateCustomerLocationView.as_view(), name='update-customer-location'),
    path('chats/inbox/', InboxContactsView.as_view(), name='inbox-contacts'),
    path('', include(router.urls)),
]
