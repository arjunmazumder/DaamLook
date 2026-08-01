from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import ActiveUser, ActiveCustomer
from .serializers import UpdateLocationSerializer, UpdateCustomerLocationSerializer
from .utils import cleanup_inactive_locations

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class UpdateLocationView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Update User Location",
        operation_description="Updates the active location (latitude/longitude) of the currently authenticated user. Call this API every 5 minutes in the background.",
        request_body=UpdateLocationSerializer,
        responses={200: "Location updated successfully"},
        tags=['Core']
    )
    
    def post(self, request):
        # Auto-cleanup locations older than 5 minutes
        cleanup_inactive_locations(minutes=5)
        
        serializer = UpdateLocationSerializer(data=request.data)
        if serializer.is_valid():
            active_user, created = ActiveUser.objects.update_or_create(
                user=request.user,
                defaults={
                    'latitude': serializer.validated_data.get('latitude'),
                    'longitude': serializer.validated_data.get('longitude')
                }
            )
            return Response(
                {"message": "Location updated successfully", "data": serializer.data}, 
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateCustomerLocationView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Update Customer Location",
        operation_description="Updates the active location (latitude/longitude) and service category of the currently authenticated customer.",
        request_body=UpdateCustomerLocationSerializer,
        responses={200: "Customer location updated successfully"},
        tags=['Core']
    )
    def post(self, request):
        # Check if the user has a role and if it's a buyer
        if not request.user.role or request.user.role.name.lower() not in ['buyer', 'buyers']:
            return Response(
                {"error": "Permission denied. Only buyers can update their location here."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # Auto-cleanup locations older than 5 minutes
        cleanup_inactive_locations(minutes=5)

        serializer = UpdateCustomerLocationSerializer(data=request.data)
        if serializer.is_valid():
            active_customer, created = ActiveCustomer.objects.update_or_create(
                user=request.user,
                defaults={
                    'category': serializer.validated_data.get('category'),
                    'latitude': serializer.validated_data.get('latitude'),
                    'longitude': serializer.validated_data.get('longitude')
                }
            )
            return Response(
                {"message": "Customer location updated successfully", "data": serializer.data}, 
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Commission
from .serializers import CommissionSerializer
from django.utils.decorators import method_decorator

@method_decorator(name='list', decorator=swagger_auto_schema(tags=['Core']))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=['Core']))
@method_decorator(name='create', decorator=swagger_auto_schema(tags=['Core']))
@method_decorator(name='update', decorator=swagger_auto_schema(tags=['Core']))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(tags=['Core']))
@method_decorator(name='destroy', decorator=swagger_auto_schema(tags=['Core']))
class CommissionViewSet(viewsets.ModelViewSet):
    """
    CRUD API for Commissions.
    """
    queryset = Commission.objects.all().order_by('-created_at')
    serializer_class = CommissionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

from rest_framework import exceptions
from django.db.models import Q
from .models import GlobalChatSession, GlobalChatMessage
from .serializers import GlobalChatSessionSerializer, GlobalChatMessageSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

chat_type_param = openapi.Parameter(
    'chat_type', openapi.IN_QUERY, description="Filter sessions by type: VENDOR or SERVICE", type=openapi.TYPE_STRING
)

@method_decorator(name='list', decorator=swagger_auto_schema(tags=['Chatting System'], manual_parameters=[chat_type_param]))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=['Chatting System']))
@method_decorator(name='create', decorator=swagger_auto_schema(tags=['Chatting System']))
@method_decorator(name='update', decorator=swagger_auto_schema(tags=['Chatting System']))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(tags=['Chatting System']))
@method_decorator(name='destroy', decorator=swagger_auto_schema(tags=['Chatting System']))
class GlobalChatSessionViewSet(viewsets.ModelViewSet):
    serializer_class = GlobalChatSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return GlobalChatSession.objects.none()
        
        user = self.request.user
        if not user.is_authenticated:
            return GlobalChatSession.objects.none()

        qs = GlobalChatSession.objects.filter(Q(buyer=user) | Q(seller=user)).order_by('-updated_at')
        chat_type = self.request.query_params.get('chat_type')
        if chat_type:
            qs = qs.filter(chat_type=chat_type.upper())
        return qs

    def perform_create(self, serializer):
        seller = serializer.validated_data.get('seller')
        if seller == self.request.user:
            raise exceptions.ValidationError({"error": "You cannot chat with yourself."})
        serializer.save(buyer=self.request.user)

session_id_param = openapi.Parameter(
    'session_id', openapi.IN_QUERY, description="ID of the chat session to filter messages", type=openapi.TYPE_INTEGER
)

@method_decorator(name='list', decorator=swagger_auto_schema(tags=['Chatting System'], manual_parameters=[session_id_param]))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=['Chatting System']))
@method_decorator(name='create', decorator=swagger_auto_schema(tags=['Chatting System']))
@method_decorator(name='update', decorator=swagger_auto_schema(tags=['Chatting System']))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(tags=['Chatting System']))
@method_decorator(name='destroy', decorator=swagger_auto_schema(tags=['Chatting System']))
class GlobalChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = GlobalChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return GlobalChatMessage.objects.none()
        
        user = self.request.user
        if not user.is_authenticated:
            return GlobalChatMessage.objects.none()

        session_id = self.request.query_params.get('session_id')
        
        qs = GlobalChatMessage.objects.filter(
            Q(session__buyer=user) | Q(session__seller=user)
        )
        if session_id:
            qs = qs.filter(session_id=session_id)
        return qs

    def perform_create(self, serializer):
        session = serializer.validated_data.get('session')
        user = self.request.user

        if session.buyer != user and session.seller != user:
            raise exceptions.PermissionDenied("You are not part of this chat session.")

        message = serializer.save(sender=user)

        # Broadcast the message to the WebSocket group so the other person gets it instantly
        channel_layer = get_channel_layer()
        room_group_name = f'global_chat_{session.id}'
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'chat_message',
                'id': message.id,
                'message': message.message,
                'message_type': message.message_type,
                'sender_id': message.sender.id,
                'timestamp': str(message.timestamp)
            }
        )

class InboxContactsView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get WhatsApp-like Inbox",
        operation_description="Returns a dedicated WhatsApp-like list of people the user is chatting with, ordered by most recent message.",
        manual_parameters=[
            openapi.Parameter('chat_type', openapi.IN_QUERY, description="Optional. Filter by VENDOR or SERVICE", type=openapi.TYPE_STRING)
        ],
        tags=['Chatting System']
    )
    def get(self, request):
        user = request.user
        qs = GlobalChatSession.objects.filter(Q(buyer=user) | Q(seller=user)).order_by('-updated_at')
        
        chat_type = request.query_params.get('chat_type')
        if chat_type:
            qs = qs.filter(chat_type=chat_type.upper())
            
        data = []
        for session in qs:
            is_buyer = session.buyer == user
            contact_user = session.seller if is_buyer else session.buyer
            
            latest_msg = session.messages.first()
            latest_msg_data = None
            if latest_msg:
                latest_msg_data = {
                    "id": latest_msg.id,
                    "message": latest_msg.message,
                    "message_type": latest_msg.message_type,
                    "timestamp": latest_msg.timestamp,
                    "is_read": latest_msg.is_read,
                    "sender_id": latest_msg.sender_id
                }
                
            unread_count = session.messages.filter(is_read=False).exclude(sender=user).count()
            
            data.append({
                "session_id": session.id,
                "chat_type": session.chat_type,
                "contact_id": contact_user.id,
                "contact_phone": getattr(contact_user, 'phone_number', getattr(contact_user, 'username', str(contact_user.id))),
                "contact_role": "SELLER" if is_buyer else "BUYER",
                "updated_at": session.updated_at,
                "unread_count": unread_count,
                "latest_message": latest_msg_data
            })
            
        return Response(data, status=status.HTTP_200_OK)
