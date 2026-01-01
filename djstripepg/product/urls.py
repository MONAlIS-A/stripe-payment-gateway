from django.urls import path
from . import views

urlpatterns = [
    path('', views.ProductListView.as_view(), name='product_list'),
    path('checkout/<int:product_id>/', views.CheckoutView.as_view(), name='checkout'),
    path('success/', views.success, name='success'),
    path('cancel/', views.cancel, name='cancel'),
    path('create-payment/<int:product_id>/', views.CreatePaymentView.as_view(), name='create_payment'),
    path('stripe-webhook/', views.StripeWebhookView.as_view(), name='stripe_webhook'),
]