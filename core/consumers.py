import json
import jwt
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings
from .models import GlobalChatSession, GlobalChatMessage
from django.contrib.auth import get_user_model

User = get_user_model()

class GlobalChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'global_chat_{self.session_id}'

        # Try to authenticate via JWT token in query string (for Vendors)
        query_string = self.scope.get('query_string', b'').decode()
        token = None
        for param in query_string.split('&'):
            if param.startswith('token='):
                token = param.split('=')[1]
                break

        if token:
            self.user = await self.get_user_from_token(token)
        else:
            # Fallback to scope user (from JWTAuthMiddleware for Services/Buyers)
            self.user = self.scope.get('user')

        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        # Check if session exists and user is part of it
        session = await self.get_session(self.session_id)
        if not session:
            await self.close()
            return

        if self.user.id != session.buyer_id and self.user.id != session.seller_id:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '')
        message_type = text_data_json.get('message_type', 'TEXT')

        if not message and message_type == 'TEXT':
            return

        # Save message to database
        saved_message = await self.save_message(self.session_id, self.user, message, message_type)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'id': saved_message.id,
                'message': saved_message.message,
                'message_type': saved_message.message_type,
                'sender_id': self.user.id,
                'timestamp': str(saved_message.timestamp)
            }
        )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'id': event['id'],
            'message': event['message'],
            'message_type': event['message_type'],
            'sender_id': event['sender_id'],
            'timestamp': event['timestamp']
        }, ensure_ascii=False))

    async def invoice_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'invoice_update',
            'invoice_id': event['invoice_id'],
            'status': event['status']
        }, ensure_ascii=False))

    @database_sync_to_async
    def get_user_from_token(self, token):
        if not token: return None
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            return User.objects.get(id=payload['user_id'])
        except Exception:
            return None

    @database_sync_to_async
    def get_session(self, session_id):
        try:
            return GlobalChatSession.objects.get(id=session_id)
        except GlobalChatSession.DoesNotExist:
            return None

    @database_sync_to_async
    def save_message(self, session_id, user, message, message_type):
        return GlobalChatMessage.objects.create(
            session_id=session_id,
            sender=user,
            message=message,
            message_type=message_type
        )
