from rest_framework import serializers
from .models import User, Product, Order, OrderItem, Payment, Notification
from django.contrib.auth.password_validation import validate_password

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'is_vendor', 'first_name', 'last_name', 'address', 'phone')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
class ProductSerializer(serializers.ModelSerializer):
    vendor = serializers.ReadOnlyField(source='vendor.id')

    class Meta:
        model = Product
        fields = ('id','vendor','name','description','price','stock','image','created_at')

class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = OrderItem
        fields = ('id','product','quantity','price')

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    customer = serializers.ReadOnlyField(source='customer.id')

    class Meta:
        model = Order
        fields = ('id','customer','total_price','status','created_at','items')
        read_only_fields = ('status','created_at')

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        customer = self.context['request'].user
        order = Order.objects.create(customer=customer, **validated_data)
        total = 0
        for item in items_data:
            product = item['product']
            qty = item['quantity']
            price = product.price
            OrderItem.objects.create(order=order, product=product, quantity=qty, price=price)
            total += price * qty
            # Optional: decrease stock
            if product.stock >= qty:
                product.stock -= qty
                product.save()
            else:
                raise serializers.ValidationError(f"Product {product.id} out of stock")
        order.total_price = total
        order.save()
        return order
    
class PaymentSerializer(serializers.ModelSerializer):
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())

    class Meta:
        model = Payment
        fields = ('id','order','amount','method','status','transaction_id','created_at')
        read_only_fields = ('status','transaction_id','created_at')

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id','user','message','is_read','created_at')
        read_only_fields = ('user','created_at')

