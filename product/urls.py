from django.urls import path

from product.views import ClassDetailView

urlpatterns = [
    path('/<int:product_id>/challenge', ClassDetailView.as_view(), name='class_detail')
]