from django.db import models

class User(models.Model):
    name                   = models.CharField(max_length=50)
    nick_name              = models.CharField(max_length=50, null=True)
    email                  = models.EmailField(max_length=100)
    password               = models.CharField(max_length=200, null=True)
    phone_number           = models.CharField(max_length=50)
    is_creator             = models.BooleanField(default=False, null=True)
    profile_image          = models.URLField(max_length=1000, null=True)
    is_benefit             = models.BooleanField(default=False)
    point                  = models.IntegerField(default=0)
    etc_channel            = models.CharField(max_length=50, null=True)
    recommend              = models.ForeignKey('self', on_delete=models.SET_NULL, null=True)
    application_channel    = models.ForeignKey('user.ApplyChannel', on_delete=models.SET_NULL, null=True)
    coupon                 = models.ManyToManyField('user.Coupon', through='user.UserCoupon')
    recently_view          = models.ManyToManyField('product.Product', through='user.RecentlyView', related_name='product_view_user')
    user_product           = models.ManyToManyField('product.Product', through='user.UserProduct', related_name='product_buy_user')
    product_like           = models.ManyToManyField('product.Product', through='user.ProductLike', related_name='product_like_user')
    community_like         = models.ManyToManyField('product.Community', through='product.CommunityLike', related_name='community_like_user')
    kit_like               = models.ManyToManyField('kit.Kit', through='kit.KitLike')
    created_at             = models.DateTimeField(auto_now_add=True)
    updated_at             = models.DateTimeField(auto_now=True, editable=True)

    class Meta:
        db_table = 'users'

class ApplyChannel(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        db_table = 'apply_channels'

class Coupon(models.Model):
    name          = models.CharField(max_length=100)
    discount_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_kit_free   = models.BooleanField(default=False)
    expire_date   = models.DateField(null=True)
    sub_category  = models.ForeignKey('product.SubCategory', on_delete=models.SET_NULL, null=True)
    product       = models.ForeignKey('product.Product', on_delete=models.SET_NULL, null=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True, editable=True)
    
    class Meta:
        db_table = 'coupons'

class UserCoupon(models.Model):
    user   = models.ForeignKey('user.User', on_delete=models.CASCADE)
    coupon = models.ForeignKey('user.Coupon', on_delete=models.CASCADE)

    class Meta:
        db_table = 'users_coupons'

class RecentlyView(models.Model):
    user    = models.ForeignKey('user.User', on_delete=models.CASCADE)
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'recently_views'

class UserProduct(models.Model):
    user        = models.ForeignKey('user.User', on_delete=models.SET_NULL, null=True)
    product     = models.ForeignKey('product.Product', on_delete=models.CASCADE)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_products'

class ProductLike(models.Model):
    user       = models.ForeignKey('user.User', on_delete=models.CASCADE)
    product    = models.ForeignKey('product.Product', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'product_likes'
