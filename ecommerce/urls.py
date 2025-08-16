"""
URL configuration for ecommerce project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from shop import views

urlpatterns = [
    path('admin/', admin.site.urls),

    #auth
    path('auth/register/', views.register),
    path('auth/login/', views.login_view),


     # products
    path('products/', views.product_list_create),
    path('products/<int:pk>/', views.product_detail),
    # orders
    path('orders/', views.order_list_create),
    path('orders/<int:pk>/', views.order_detail),
    # payments
    path('payments/initiate/', views.initiate_payment),
    path('payments/webhook/', views.payment_webhook),
    # notifications
    path('notifications/', views.notifications_list),
    path('notifications/<int:pk>/read/', views.mark_notification_read),
]
