from django.urls import path

from product.views import ProductDetailView, MainPageView

urlpatterns = [
    path('/<int:product_id>', ProductDetailView.as_view(), name='products'),
    path('/main', MainPageView.as_view()),
]