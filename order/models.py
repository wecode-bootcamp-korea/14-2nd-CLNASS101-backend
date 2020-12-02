from django.db import models

class Order(models.Model):
    name           = models.CharField(max_length=45)
    phone_number   = models.CharField(max_length=45)
    address        = models.CharField(max_length=200)
    order_number   = models.CharField(max_length=100)
    request_option = models.CharField(max_length=45, null=True)
    order_status   = models.ForeignKey('order.OrderStatus', on_delete=models.SET_NULL, null=True)
    product        = models.ForeignKey('product.Product', on_delete=models.SET_NULL, null=True)
    kit            = models.ForeignKey('kit.Kit', on_delete=models.SET_NULL, null=True)
    coupon         = models.ForeignKey('user.Coupon', on_delete=models.SET_NULL, null=True)
    payment_method = models.ForeignKey('order.PaymentMethod', on_delete=models.SET_NULL, null=True)
    user           = models.ForeignKey('user.User', on_delete=models.SET_NULL, null=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True, editable=True)
    
    class Meta:
        db_table = 'orders'

class PaymentMethod(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        db_table = 'payment_methods'

class OrderStatus(models.Model):
    status = models.CharField(max_length=30)

    class Meta:
        db_table = 'order_statuses'
