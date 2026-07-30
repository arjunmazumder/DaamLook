from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Cart, CartItem, Order, OrderItem, VendorOrder, DeliveryCharge
from products.models import Product
from .serializers import CartSerializer, CartItemSerializer, OrderSerializer, VendorOrderSerializer
from .utils import calculate_product_unit_price

class CartViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_cart(self, user):
        cart, created = Cart.objects.get_or_create(user=user)
        return cart

    def list(self, request):
        cart = self.get_cart(request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['product_id'],
            properties={
                'product_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the product'),
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, description='Quantity to add (default 1)'),
            }
        ),
        responses={201: CartItemSerializer()}
    )
    @action(detail=False, methods=['post'])
    def add(self, request):
        cart = self.get_cart(request.user)
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        if not product_id:
            return Response({"error": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Product, id=product_id, is_active=True, approval_status='APPROVED')

        # Validation
        if product.stock_quantity < quantity:
            return Response({"error": f"Only {product.stock_quantity} items in stock"}, status=status.HTTP_400_BAD_REQUEST)
        if product.product_type == 'WHOLESALE' and quantity < product.moq:
            return Response({"error": f"Minimum order quantity is {product.moq}"}, status=status.HTTP_400_BAD_REQUEST)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity, 'unit_price': 0}
        )

        if not created:
            new_quantity = cart_item.quantity + quantity
            if product.stock_quantity < new_quantity:
                return Response({"error": f"Only {product.stock_quantity} items in stock"}, status=status.HTTP_400_BAD_REQUEST)
            cart_item.quantity = new_quantity
            
        cart_item.unit_price = calculate_product_unit_price(product, cart_item.quantity)
        cart_item.save()

        return Response(CartItemSerializer(cart_item).data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, description='New quantity'),
            }
        ),
        responses={200: CartItemSerializer()}
    )
    @action(detail=True, methods=['patch'])
    def update_quantity(self, request, pk=None):
        cart = self.get_cart(request.user)
        cart_item = get_object_or_404(CartItem, id=pk, cart=cart)
        
        quantity = int(request.data.get('quantity', cart_item.quantity))
        
        if quantity <= 0:
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        product = cart_item.product
        if product.stock_quantity < quantity:
            return Response({"error": f"Only {product.stock_quantity} items in stock"}, status=status.HTTP_400_BAD_REQUEST)
        if product.product_type == 'WHOLESALE' and quantity < product.moq:
            return Response({"error": f"Minimum order quantity is {product.moq}"}, status=status.HTTP_400_BAD_REQUEST)

        cart_item.quantity = quantity
        cart_item.unit_price = calculate_product_unit_price(product, quantity)
        cart_item.save()

        return Response(CartItemSerializer(cart_item).data)

    @action(detail=True, methods=['delete'])
    def remove(self, request, pk=None):
        cart = self.get_cart(request.user)
        cart_item = get_object_or_404(CartItem, id=pk, cart=cart)
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['delete'])
    def clear(self, request):
        cart = self.get_cart(request.user)
        cart.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    For Buyers to see their own orders.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
        return Order.objects.filter(buyer=self.request.user).order_by('-created_at')

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['buyer_city_id'],
            properties={
                'buyer_city_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the buyer selected City'),
            }
        ),
        responses={200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'cart_details': openapi.Schema(type=openapi.TYPE_OBJECT, description="Full details of the cart and its items"),
                'total_amount': openapi.Schema(type=openapi.TYPE_NUMBER),
                'total_delivery_charge': openapi.Schema(type=openapi.TYPE_NUMBER),
                'grand_total': openapi.Schema(type=openapi.TYPE_NUMBER),
                'delivery_charge_breakdown': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT))
            }
        )}
    )
    @action(detail=False, methods=['post'])
    def checkout_summary(self, request):
        user = request.user
        cart = Cart.objects.filter(user=user).first()
        
        if not cart or not cart.items.exists():
            return Response({"error": "Your cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        buyer_city_id = request.data.get('buyer_city_id')
        if not buyer_city_id:
            return Response({"error": "buyer_city_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        total_amount = 0
        unique_shops = set()

        for cart_item in cart.items.all():
            total_amount += (cart_item.quantity * cart_item.unit_price)
            if cart_item.product.shop:
                unique_shops.add(cart_item.product.shop)

        delivery_rates = DeliveryCharge.objects.first()
        total_delivery_charge = 0
        breakdown = []
        
        if delivery_rates:
            for shop in unique_shops:
                if shop.city_id and str(shop.city_id) == str(buyer_city_id):
                    charge = delivery_rates.inside_city
                else:
                    charge = delivery_rates.outside_city
                    
                total_delivery_charge += charge
                breakdown.append({
                    "shop_name": shop.shop_name,
                    "delivery_charge": charge
                })

        return Response({
            "cart_details": CartSerializer(cart).data,
            "total_amount": total_amount,
            "total_delivery_charge": total_delivery_charge,
            "grand_total": total_amount + total_delivery_charge,
            "delivery_charge_breakdown": breakdown
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('buyer_city_id', openapi.IN_QUERY, description="ID of the buyer selected City", type=openapi.TYPE_INTEGER, required=True),
        ],
        responses={200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'cart_details': openapi.Schema(type=openapi.TYPE_OBJECT, description="Full details of the cart and its items"),
                'total_amount': openapi.Schema(type=openapi.TYPE_NUMBER),
                'total_delivery_charge': openapi.Schema(type=openapi.TYPE_NUMBER),
                'grand_total': openapi.Schema(type=openapi.TYPE_NUMBER),
                'delivery_charge_breakdown': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT))
            }
        )}
    )
    @action(detail=False, methods=['get'])
    def summary_details(self, request):
        user = request.user
        cart = Cart.objects.filter(user=user).first()
        
        if not cart or not cart.items.exists():
            return Response({"error": "Your cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        buyer_city_id = request.query_params.get('buyer_city_id')
        if not buyer_city_id:
            return Response({"error": "buyer_city_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        total_amount = 0
        unique_shops = set()

        for cart_item in cart.items.all():
            total_amount += (cart_item.quantity * cart_item.unit_price)
            if cart_item.product.shop:
                unique_shops.add(cart_item.product.shop)

        delivery_rates = DeliveryCharge.objects.first()
        total_delivery_charge = 0
        breakdown = []
        
        if delivery_rates:
            for shop in unique_shops:
                if shop.city_id and str(shop.city_id) == str(buyer_city_id):
                    charge = delivery_rates.inside_city
                else:
                    charge = delivery_rates.outside_city
                    
                total_delivery_charge += charge
                breakdown.append({
                    "shop_name": shop.shop_name,
                    "delivery_charge": charge
                })

        return Response({
            "cart_details": CartSerializer(cart).data,
            "total_amount": total_amount,
            "total_delivery_charge": total_delivery_charge,
            "grand_total": total_amount + total_delivery_charge,
            "delivery_charge_breakdown": breakdown
        }, status=status.HTTP_200_OK)
    @swagger_auto_schema(
        operation_description="Checkout cart items and create an order. Automatically uses the user's saved ShippingAddress (including city).",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'payment_method': openapi.Schema(type=openapi.TYPE_STRING, description='Payment Method (COD or ONLINE)'),
            }
        ),
        responses={201: OrderSerializer()}
    )
    @action(detail=False, methods=['post'])
    def checkout(self, request):
        user = request.user
        cart = Cart.objects.filter(user=user).first()
        
        if not cart or not cart.items.exists():
            return Response({"error": "Your cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        # Automatically fetch ShippingAddress
        if not hasattr(user, 'shipping_address') or not user.shipping_address:
            return Response({"error": "Shipping address is missing. Please add a shipping address before checkout."}, status=status.HTTP_400_BAD_REQUEST)

        shipping_address = user.shipping_address.address
        contact_phone = user.shipping_address.phone_number
        buyer_city_id = user.shipping_address.city_id

        if not buyer_city_id:
            return Response({"error": "Your shipping address is missing a city. Please update your shipping address."}, status=status.HTTP_400_BAD_REQUEST)

        payment_method = request.data.get('payment_method', 'COD')

        # Create main order
        order = Order.objects.create(
            buyer=user,
            buyer_city_id=buyer_city_id,
            shipping_address=shipping_address,
            contact_phone=contact_phone,
            payment_method=payment_method,
            status='PENDING_ADMIN_APPROVAL'
        )

        total_amount = 0
        unique_shops = set()

        # Copy items to OrderItem
        for cart_item in cart.items.all():
            product = cart_item.product
            # Final validation
            if product.stock_quantity < cart_item.quantity:
                order.delete()
                return Response({"error": f"Product '{product.title}' only has {product.stock_quantity} in stock"}, status=status.HTTP_400_BAD_REQUEST)
                
            OrderItem.objects.create(
                order=order,
                product=product,
                shop=product.shop,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price
            )
            total_amount += (cart_item.quantity * cart_item.unit_price)
            unique_shops.add(product.shop)

        # Calculate Delivery Charge
        delivery_rates = DeliveryCharge.objects.first()
        total_delivery_charge = 0
        if delivery_rates:
            for shop in unique_shops:
                if shop.city_id and str(shop.city_id) == str(buyer_city_id):
                    total_delivery_charge += delivery_rates.inside_city
                else:
                    total_delivery_charge += delivery_rates.outside_city

        order.total_delivery_charge = total_delivery_charge
        order.total_amount = total_amount
        order.save()

        # Clear cart
        cart.items.all().delete()

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class AdminOrderViewSet(viewsets.ModelViewSet):
    """
    For Admins to manage all orders.
    """
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAdminUser]

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        order = self.get_object()
        
        if order.status != 'PENDING_ADMIN_APPROVAL':
            return Response({"error": f"Order is already {order.status}"}, status=status.HTTP_400_BAD_REQUEST)

        # Group items by shop and create VendorOrders
        shop_items = {}
        for item in order.items.all():
            if item.shop not in shop_items:
                shop_items[item.shop] = []
            shop_items[item.shop].append(item)

        delivery_rates = DeliveryCharge.objects.first()

        for shop, items in shop_items.items():
            subtotal = sum(i.quantity * i.unit_price for i in items)
            
            # Calculate this specific shop's delivery charge
            delivery_charge = 0
            if delivery_rates:
                if shop.city_id and str(shop.city_id) == str(order.buyer_city_id):
                    delivery_charge = delivery_rates.inside_city
                else:
                    delivery_charge = delivery_rates.outside_city
                    
            vendor_order = VendorOrder.objects.create(
                parent_order=order,
                vendor_shop=shop,
                subtotal_amount=subtotal,
                delivery_charge=delivery_charge,
                status='PROCESSING'
            )
            # Update items to link to this vendor order
            for item in items:
                item.vendor_order = vendor_order
                item.save()
                
                # Deduct stock ONLY upon approval
                if item.product:
                    item.product.stock_quantity -= item.quantity
                    item.product.save()

        order.status = 'APPROVED'
        order.save()

        return Response({"message": "Order approved, stock deducted, and forwarded to vendors."})

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'rejection_reason': openapi.Schema(type=openapi.TYPE_STRING, description='Reason for rejection'),
            }
        ),
        responses={200: openapi.Response('Order rejected')}
    )
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        order = self.get_object()
        rejection_reason = request.data.get('rejection_reason', 'No reason provided')
        
        if order.status != 'PENDING_ADMIN_APPROVAL':
            return Response({"error": f"Order is already {order.status}"}, status=status.HTTP_400_BAD_REQUEST)

        order.status = 'REJECTED'
        order.rejection_reason = rejection_reason
        order.save()

        return Response({"message": "Order rejected."})


class VendorOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    For Vendors to view and update their own sub-orders.
    """
    serializer_class = VendorOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return VendorOrder.objects.none()
        
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return VendorOrder.objects.all().order_by('-created_at')
            
        return VendorOrder.objects.filter(vendor_shop__user=user).order_by('-created_at')

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['status'],
            properties={
                'status': openapi.Schema(type=openapi.TYPE_STRING, description='New status (PROCESSING, PACKED, SHIPPED, DELIVERED, CANCELLED)'),
            }
        ),
        responses={200: VendorOrderSerializer()}
    )
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        vendor_order = self.get_object()
        new_status = request.data.get('status')
        
        valid_statuses = [c[0] for c in VendorOrder.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)
            
        vendor_order.status = new_status
        vendor_order.save()
        
        return Response(VendorOrderSerializer(vendor_order).data)

from django.utils.decorators import method_decorator
from .serializers import DeliveryChargeSerializer

@method_decorator(name='list', decorator=swagger_auto_schema(tags=['DeliveryCharge']))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=['DeliveryCharge']))
@method_decorator(name='create', decorator=swagger_auto_schema(tags=['DeliveryCharge']))
@method_decorator(name='update', decorator=swagger_auto_schema(tags=['DeliveryCharge']))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(tags=['DeliveryCharge']))
@method_decorator(name='destroy', decorator=swagger_auto_schema(tags=['DeliveryCharge']))
class DeliveryChargeViewSet(viewsets.ModelViewSet):
    """
    CRUD API for Delivery Charges.
    """
    queryset = DeliveryCharge.objects.all()
    serializer_class = DeliveryChargeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

from .models import OrderCommission
from .serializers import OrderCommissionSerializer

class OrderCommissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API for Order Commissions.
    Admins see all, Vendors see commissions for their shop.
    """
    serializer_class = OrderCommissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return OrderCommission.objects.none()

        user = self.request.user
        if not user.is_authenticated:
            return OrderCommission.objects.none()

        if user.is_staff or user.is_superuser:
            return OrderCommission.objects.all().order_by('-created_at')
            
        if hasattr(user, 'business_profile'):
            return OrderCommission.objects.filter(
                order_item__shop=user.business_profile
            ).order_by('-created_at')
            
        return OrderCommission.objects.none()
