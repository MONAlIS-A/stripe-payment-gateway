from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from . models import Product, Order
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY


class ProductListView(View):
    def get(self, request):
        products = Product.objects.all()
        return render(request, 'product/product_list.html', {'products': products})
    
class CheckoutView(LoginRequiredMixin, View):
    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        return render(request, 'product/checkout.html', {'product': product})
    
def success(request):
    return JsonResponse({'status': 'success'})

def cancel(request):
    return JsonResponse({'status': 'cancel'})

@method_decorator(csrf_exempt, name='dispatch')
class CreatePaymentView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        order = Order.objects.create(
            user=request.user,
            product=product,
            amount=product.price,
            is_paid=False
        )
        checkout_session = stripe.checkout.Session.create(
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': product.name,
                    },
                    'unit_amount': int(product.price * 100),
                },
                'quantity': 1,

            }],
            mode='payment',
            customer_email=request.user.email,
            success_url= 'http://localhost:8000/success',
            cancel_url= 'http://localhost:8000/cancel',
        )
        order.stripe_checkout_session_id = checkout_session.id
        order.save()

        return redirect(checkout_session.url)
    

@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')  
        endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET')  

        if not endpoint_secret:
            return JsonResponse({'error': 'Webhook secret not configured'}, status=500)

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError:
            return JsonResponse({'status': 'invalid payload'}, status=400)
        except stripe.error.SignatureVerificationError:
            return JsonResponse({'status': 'invalid signature'}, status=400)

        if event['type'] == 'checkout.session.completed':
            print(event)
            session = event['data']['object']
            order = get_object_or_404(Order, stripe_checkout_session_id=session['id'])
            order.is_paid = True
            order.save()

        return JsonResponse({'status': 'success'})
