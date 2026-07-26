from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/vendors/chats/(?P<session_id>\d+)/?$', consumers.VendorChatConsumer.as_asgi()),
]
