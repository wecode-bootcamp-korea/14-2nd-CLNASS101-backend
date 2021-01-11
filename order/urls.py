from django.urls import path

from order.views import SelectProductAndPaymentView, OrderProductView

urlpatterns = [
    path('/select-class-and-payment', SelectProductAndPaymentView.as_view(), name='apply_product'),
    path('/order', OrderProductView.as_view(), name='payment_product')
]