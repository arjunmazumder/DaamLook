import json
import jwt
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model
User = get_user_model()
from .models import VendorChatSession, VendorChatMessage

class VendorChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'vendor_chat_{self.session_id}'

        # Authenticate via JWT token in query string
        query_string = self.scope['query_string'].decode()
        token = None
        for param in query_string.split('&'):
            if param.startswith('token='):
                token = param.split('=')[1]
                break

        self.user = await self.get_user_from_token(token)
        if self.user is None:
            await self.close()
            return

        # Check if user is part of the session
        is_participant = await self.is_participant(self.session_id, self.user)
        if not is_participant:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message')
        message_type = data.get('message_type', 'TEXT')

        if not message and message_type == 'TEXT':
            return

        # Save message to DB
        chat_msg = await self.save_message(self.session_id, self.user, message, message_type)

        # Broadcast to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'id': chat_msg.id,
                'message': chat_msg.message,
                'message_type': chat_msg.message_type,
                'sender_id': str(chat_msg.sender.id),
                'timestamp': str(chat_msg.timestamp)
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'id': event['id'],
            'message': event['message'],
            'message_type': event['message_type'],
            'sender_id': event['sender_id'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def get_user_from_token(self, token):
        if not token: return None
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            return User.objects.get(id=payload['user_id'])
        except Exception:
            return None

    @database_sync_to_async
    def is_participant(self, session_id, user):
        try:
            session = VendorChatSession.objects.get(id=session_id)
            return session.buyer == user or session.vendor.user == user
        except VendorChatSession.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, session_id, user, message, message_type):
        session = VendorChatSession.objects.get(id=session_id)
        return VendorChatMessage.objects.create(
            session=session,
            sender=user,
            message=message,
            message_type=message_type
        )
