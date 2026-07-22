import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatSession, ChatMessage
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'chat_{self.session_id}'
        self.user = self.scope.get('user')

        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        # Check if session exists and user is part of it
        session = await self.get_session(self.session_id)
        if not session:
            await self.close()
            return

        is_participant = False
        if self.user.id == session.buyer_id:
            is_participant = True
        else:
            has_profile, profile_id = await self.get_user_business_profile_id(self.user)
            if has_profile and profile_id == session.provider_id:
                is_participant = True
        
        if not is_participant:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
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

    # Receive message from room group
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'id': event['id'],
            'message': event['message'],
            'message_type': event['message_type'],
            'sender_id': event['sender_id'],
            'timestamp': event['timestamp']
        }, ensure_ascii=False))

    @database_sync_to_async
    def get_session(self, session_id):
        try:
            return ChatSession.objects.select_related('buyer', 'provider').get(id=session_id)
        except ChatSession.DoesNotExist:
            return None

    @database_sync_to_async
    def get_user_business_profile_id(self, user):
        try:
            profile = user.business_profile
            return True, profile.id
        except Exception:
            return False, None

    @database_sync_to_async
    def save_message(self, session_id, user, message, message_type):
        return ChatMessage.objects.create(
            session_id=session_id,
            sender=user,
            message=message,
            message_type=message_type
        )

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get('user')

        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        # Connect the user to their personal notification group
        self.room_group_name = f'notifications_{self.user.id}'

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

    # Receive message from room group
    async def notification_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'notification_id': event.get('notification_id'),
            'message': event.get('message'),
            'booking_id': event.get('booking_id'),
            'type': 'NOTIFICATION'
        }, ensure_ascii=False))
