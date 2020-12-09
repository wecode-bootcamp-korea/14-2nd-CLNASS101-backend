from django.urls import path

from order.views import SelectProductAndPaymentView

urlpatterns = [
    path('/select-class-and-payment', SelectProductAndPaymentView.as_view(), name='apply_product'),
]