import json

from django.views   import View
from django.http    import JsonResponse

from product.models import Product
from user.models    import User, UserCoupon
from core.utils     import login_decorator

class SelectProductAndPaymentView(View):
    
    @login_decorator(view_name='SelectProductAndPaymentView')
    def get(self, request, product_id):
        try:
            user = User.objects.get(id=request.user.id)
            
            product = Product.objects.get(id=product_id)
            
            user_coupons = \
                UserCoupon.objects.filter(user_id=user.id).select_related('coupon')
            
            order_info = {
                'className'      : product.name,
                'classId'        : product.id,
                'userName'       : user.name,
                'userPhoneNumber': user.phone_number,
                'userId'         : user.id,
                'originalPrice'  : '{:,}원'.format(int(product.price)),
                'discountPrice'  : '{:,}원'.format(int(product.price * product.sale) * -1),
                'discountedPrice': '{:,}원'.format(int((1 - product.sale) * product.price)),
                'couponInfo'     : [
                    {
                        'userCouponId'     : user_coupon.id,
                        'couponName'       : user_coupon.coupon.name,
                        'couponDiscount'   : '{:,}원'.format(int(user_coupon.coupon.discount_cost)),
                        'couponExpiredDate': '무제한' if not user_coupon.coupon.expire_date else
                                             user_coupon.coupon.expire_date
                    } for user_coupon in user_coupons
                ]
            }
        
        except Product.DoesNotExist:
            return JsonResponse({'MESSAGE': 'PRODUCT_NOT_EXIST'}, status=400)
        
        return JsonResponse({'ORDER_INFO': order_info}, status=200)