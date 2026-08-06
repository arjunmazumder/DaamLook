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
        if not request.user.role or request.user.role.value.lower() not in ['buyer', 'buyers']:
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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        seller = serializer.validated_data.get('seller')
        chat_type = serializer.validated_data.get('chat_type')
        buyer = request.user
        
        if seller == buyer:
            return Response({"error": "You cannot chat with yourself."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Check if session already exists
        session, created = GlobalChatSession.objects.get_or_create(
            buyer=buyer,
            seller=seller,
            chat_type=chat_type,
            defaults={'is_active': True}
        )
        
        resp_serializer = self.get_serializer(session)
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(resp_serializer.data, status=response_status)

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

    def list(self, request, *args, **kwargs):
        session_id = request.query_params.get('session_id')
        if session_id and request.user.is_authenticated:
            # When the user opens the chat and fetches messages, mark unread messages from the other user as read.
            GlobalChatMessage.objects.filter(
                session_id=session_id,
                is_read=False
            ).exclude(sender=request.user).update(is_read=True)
        return super().list(request, *args, **kwargs)

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
            
            # Explicit buyer name
            buyer_name = getattr(session.buyer, 'full_name', '')
            if not buyer_name:
                buyer_name = getattr(session.buyer, 'phone_number', getattr(session.buyer, 'username', str(session.buyer.id)))
                
            # Explicit shop name and image
            shop_name = ""
            shop_image = None
            if session.chat_type == 'VENDOR' and hasattr(session.seller, 'vendor_shop_profile'):
                shop_name = getattr(session.seller.vendor_shop_profile, 'shop_name', '')
                if session.seller.vendor_shop_profile.logo:
                    shop_image = request.build_absolute_uri(session.seller.vendor_shop_profile.logo.url)
            elif session.chat_type == 'SERVICE' and hasattr(session.seller, 'business_profile'):
                shop_name = getattr(session.seller.business_profile, 'shop_name', '')

            contact_name = getattr(contact_user, 'full_name', '')
            if not contact_name:
                contact_name = getattr(contact_user, 'phone_number', getattr(contact_user, 'username', str(contact_user.id)))
                
            contact_image = None

            if is_buyer: # Contact is seller
                if shop_name:
                    contact_name = shop_name
                if shop_image:
                    contact_image = shop_image

            if not contact_image and hasattr(contact_user, 'kyc_profile') and contact_user.kyc_profile.profile_img:
                contact_image = request.build_absolute_uri(contact_user.kyc_profile.profile_img.url)
            
            data.append({
                "session_id": session.id,
                "chat_type": session.chat_type,
                "buyer_name": buyer_name,
                "shop_name": shop_name,
                "shop_image": shop_image,
                "contact_id": contact_user.id,
                "contact_name": contact_name,
                "contact_image": contact_image,
                "contact_phone": getattr(contact_user, 'phone_number', getattr(contact_user, 'username', str(contact_user.id))),
                "contact_role": "SELLER" if is_buyer else "BUYER",
                "updated_at": session.updated_at,
                "unread_count": unread_count,
                "latest_message": latest_msg_data
            })
            
        return Response(data, status=status.HTTP_200_OK)

from rest_framework.decorators import action
from orders.models import ChatSessionInvoice, ChatSessionInvoiceCommission
from .serializers import ChatSessionInvoiceSerializer, ChatSessionInvoiceCommissionSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=['Chatting System - Invoices']))
@method_decorator(name='create', decorator=swagger_auto_schema(tags=['Chatting System - Invoices']))
@method_decorator(name='update', decorator=swagger_auto_schema(tags=['Chatting System - Invoices']))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(tags=['Chatting System - Invoices']))
@method_decorator(name='destroy', decorator=swagger_auto_schema(tags=['Chatting System - Invoices']))
class ChatSessionInvoiceViewSet(viewsets.ModelViewSet):
    """
    API for Vendors to create invoices inside a chat, and for Buyers to confirm or reject them.
    """
    queryset = ChatSessionInvoice.objects.all().order_by('-created_at')
    serializer_class = ChatSessionInvoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ChatSessionInvoice.objects.none()
        
        user = self.request.user
        if not user.is_authenticated:
            return ChatSessionInvoice.objects.none()
            
        if user.is_superuser or getattr(user.role, 'name', '') in ['Admin', 'Super Admin']:
            qs = ChatSessionInvoice.objects.all().order_by('-created_at')
        else:
            qs = ChatSessionInvoice.objects.filter(
                Q(session__buyer=user) | Q(session__seller=user)
            ).order_by('-created_at')

        session_id = self.request.query_params.get('session_id')
        if session_id:
            qs = qs.filter(session__id=session_id)
            
        return qs

    @swagger_auto_schema(
        operation_summary="List Invoices",
        manual_parameters=[
            openapi.Parameter('session_id', openapi.IN_QUERY, description="Filter invoices by Chat Session ID", type=openapi.TYPE_INTEGER)
        ],
        tags=['Chatting System - Invoices']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        session = serializer.validated_data.get('session')
        user = self.request.user

        if session.seller != user:
            raise exceptions.PermissionDenied("Only the vendor (seller) can create an invoice for this session.")
            
        serializer.save()

    @swagger_auto_schema(operation_summary="Confirm Chat Invoice (Buyer Only)", tags=['Chatting System - Invoices'])
    @action(detail=True, methods=['patch'])
    def confirm(self, request, pk=None):
        invoice = self.get_object()
        user = request.user
        
        if invoice.session.buyer != user:
            return Response({"error": "Only the buyer can confirm this invoice."}, status=status.HTTP_403_FORBIDDEN)
            
        if invoice.status != 'PENDING':
            return Response({"error": "Only pending invoices can be confirmed."}, status=status.HTTP_400_BAD_REQUEST)
            
        invoice.status = 'CONFIRMED'
        invoice.save()

        # Notify via WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'global_chat_{invoice.session.id}',
            {
                'type': 'invoice_update',
                'invoice_id': invoice.id,
                'status': invoice.status
            }
        )

        return Response({"message": "Invoice confirmed successfully.", "status": invoice.status})

    @swagger_auto_schema(operation_summary="Reject Chat Invoice (Buyer Only)", tags=['Chatting System - Invoices'])
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    def reject(self, request, pk=None):
        invoice = self.get_object()
        if invoice.session.buyer != request.user:
            return Response({"error": "Only the buyer can reject the invoice."}, status=status.HTTP_403_FORBIDDEN)
            
        if invoice.status != 'PENDING':
            return Response({"error": "Only pending invoices can be rejected."}, status=status.HTTP_400_BAD_REQUEST)
            
        invoice.status = 'REJECTED'
        invoice.save()

        # Notify via WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'global_chat_{invoice.session.id}',
            {
                'type': 'invoice_update',
                'invoice_id': invoice.id,
                'status': invoice.status
            }
        )

        return Response({"message": "Invoice rejected.", "status": invoice.status})

@method_decorator(name='list', decorator=swagger_auto_schema(tags=['Chatting System - Invoices']))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=['Chatting System - Invoices']))
class ChatSessionInvoiceCommissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API to view commissions automatically generated from Chat Session Invoices.
    """
    queryset = ChatSessionInvoiceCommission.objects.all().order_by('-created_at')
    serializer_class = ChatSessionInvoiceCommissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ChatSessionInvoiceCommission.objects.none()
            
        user = self.request.user
        if not user.is_authenticated:
            return ChatSessionInvoiceCommission.objects.none()
            
        if user.is_superuser or getattr(user.role, 'name', '') in ['Admin', 'Super Admin']:
            return ChatSessionInvoiceCommission.objects.all().order_by('-created_at')
            
        return ChatSessionInvoiceCommission.objects.filter(invoice__session__seller=user).order_by('-created_at')
