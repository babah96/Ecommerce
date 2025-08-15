from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    is_vendor = models.BooleanField(default=False)
    address = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.username
    
class Product(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=10)
    image = models.ImageField(upload_to='products/',blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.vendor.username}"
    
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending' , 'pending'),
        ('paid', 'paid'),
        ('shipped', 'shipped'),
        ('cancelled', 'cancelled'),

    ]
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    total_price = models.DecimalField(max_digits=)