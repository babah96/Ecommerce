from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .models import Product, Order, Payment, Notification
from .serializers import (UserSerializer, ProductSerializer, OrderSerializer,
                          PaymentSerializer, NotificationSerializer)
from django.shortcuts import get_object_or_404

# --- Authentication endpoints ---
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        data = serializer.data
        data['token'] = token.key
        return Response(data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user_id': user.id})
    return Response({'detail':'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

# --- Products ---
@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
def product_list_create(request):
    if request.method == 'GET':
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        data = request.data.copy()
        # set vendor to current user; only vendors allowed to create
        if not request.user.is_vendor:
            return Response({'detail':'Only vendors can create products'}, status=status.HTTP_403_FORBIDDEN)
        data['vendor'] = request.user.id
        serializer = ProductSerializer(data=data)
        if serializer.is_valid():
            serializer.save(vendor=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','PUT','DELETE'])
@permission_classes([IsAuthenticated])
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'GET':
        serializer = ProductSerializer(product)
        return Response(serializer.data)
    if request.method == 'PUT':
        if product.vendor != request.user:
            return Response({'detail':'Not allowed'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    if request.method == 'DELETE':
        if product.vendor != request.user:
            return Response({'detail':'Not allowed'}, status=status.HTTP_403_FORBIDDEN)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# --- Orders ---
@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
def order_list_create(request):
    if request.method == 'GET':
        # customers see own orders; vendors see orders containing their products
        if request.user.is_vendor:
            orders = Order.objects.filter(items__product__vendor=request.user).distinct()
        else:
            orders = Order.objects.filter(customer=request.user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        data = request.data.copy()
        serializer = OrderSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            order = serializer.save()
            # send notification to vendors and customer
            Notification.objects.create(user=request.user, message=f"Order {order.id} created")
            # For each vendor involved, create a notification (simplified)
            vendor_ids = set([item.product.vendor for item in order.items.all()])
            for v in vendor_ids:
                Notification.objects.create(user=v, message=f"New order {order.id} includes your products")
            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.user != order.customer and not request.user.is_vendor:
        # vendors can view only if they have products in the order
        if not order.items.filter(product__vendor=request.user).exists():
            return Response({'detail':'Not allowed'}, status=status.HTTP_403_FORBIDDEN)
    serializer = OrderSerializer(order)
    return Response(serializer.data)

# --- Payments (stubbed) ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_payment(request):
    # Expected: { "order": order_id, "method": "stripe" }
    serializer = PaymentSerializer(data=request.data)
    if serializer.is_valid():
        payment = serializer.save()
        # In real implementation: create Stripe Checkout session and return session id
        payment.status = 'pending'
        payment.save()
        # Notify customer
        Notification.objects.create(user=payment.order.customer, message=f"Payment initiated for order {payment.order.id}")
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# webhook endpoint to be called by payment provider (example)
@api_view(['POST'])
@permission_classes([AllowAny])
def payment_webhook(request):
    # Verify signature in production
    event = request.data.get('type')
    data = request.data.get('data', {})
    # Example handling
    if event == 'payment.succeeded':
        order_id = data.get('order_id')
        try:
            order = Order.objects.get(pk=order_id)
            order.status = 'paid'
            order.save()
            Notification.objects.create(user=order.customer, message=f"Payment received for order {order.id}")
            return Response({'status':'ok'})
        except Order.DoesNotExist:
            return Response({'detail':'order not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response({'status':'ignored'})

# --- Notifications (REST) ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notifications_list(request):
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')
    serializer = NotificationSerializer(notifs, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save()
    return Response({'status':'ok'})
