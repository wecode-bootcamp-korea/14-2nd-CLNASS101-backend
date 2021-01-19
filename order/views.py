import json
from datetime import datetime, date

from django.views import View
from django.http import JsonResponse
from django.db import IntegrityError, transaction

from product.models import Product
from user.models import User, UserCoupon, UserProduct
from order.models import Order, OrderStatus, PaymentMethod
from core.utils import login_decorator

class SelectProductAndPaymentView(View):
    
    @login_decorator(login_required=True)
    def get(self, request, product_id):
        try:
            user = request.user
            product = Product.objects.get(id=product_id)
            user_coupons = user.usercoupon_set.all()
            
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

class OrderProductView(View):
    
    @transaction.atomic
    @login_decorator(login_required=True)
    def post(self, request, product_id):
        payload = json.loads(request.body)
        
        try:
            if not isinstance(product_id, int):
                raise ValueError
            
            user_name = payload['user_name']
            phone_number = payload['phone_number']
            post_number = payload['post_number']
            address = payload['address']
            sub_address = payload['sub_address']
            request_option = payload['request_option']
            coupon_id = payload['coupon_id']
            price = payload['price']
            payment_method_id = payload['payment_method_id']
            
            if is_all_blank(
                request.user, product_id, user_name, phone_number, price, payment_method_id
            ):
                raise RequiredInputException
            
            if Product.objects.get(id=product_id).kit.exists():
                
                if is_all_blank(post_number, address, sub_address):
                    raise RequiredInputException
            
            user = request.user
            
            if not UserProduct.objects.filter(
                user_id=user.id,
                product_id=product_id
            ).exists():
                
                user.user_product.add(Product.objects.get(id=product_id))
            
            else:
                product_effective_time = Product.objects.get(id=product_id).effective_time
                
                if not product_effective_time:
                    raise PermanentProductException
                
                purchased_date = \
                    UserProduct.objects.get(
                        user_id=user.id,
                        product_id=product_id
                    ).created_at
                
                if purchased_date + product_effective_time > date.today():
                    raise AlreadyOwnedProductException
                
                UserProduct.objects.filter(
                    user_id=user.id,
                    product_id=product_id
                ).update(created_at=datetime.today())
            
            try:
                with transaction.atomic():
                    Order.objects.create(
                        name=user_name,
                        phone_number=phone_number,
                        address=f'{address} {sub_address} {post_number}',
                        order_number=generate_order_number(
                            datetime.now(),
                            Order.objects.count() + 1
                        ),
                        request_option=request_option,
                        order_status=OrderStatus.objects.get(id=7),
                        product_id=product_id,
                        kit=None,
                        coupon=coupon_id,
                        payment_method=PaymentMethod.objects.get(id=payment_method_id),
                        user_id=user.id
                    )
                    
                    if coupon_id:
                        UserCoupon.objects.filter(
                            user_id=user.id,
                            coupon_id=coupon_id
                        ).delete()
                    
                    user.point += int(price * 0.03)
                    user.save()
            
            except IntegrityError:
                return JsonResponse({"MESSAGE": "TRANSACTION_ERROR"}, status=400)
            
            return JsonResponse({'MESSAGE': 'ORDER_SUCCESS'}, status=200)
        
        except KeyError:
            return JsonResponse({'MESSAGE': 'KEY_ERROR'}, status=400)
        
        except RequiredInputException as e:
            return JsonResponse({'MESSAGE': e.__str__()}, status=400)
        
        except ValueError:
            return JsonResponse({'MESSAGE': 'VALUE_ERROR'}, status=400)
        
        except PermanentProductException as e:
            return JsonResponse({'MESSAGE': e.__str__()}, status=400)
        
        except AlreadyOwnedProductException as e:
            return JsonResponse({'MESSAGE': e.__str__()}, status=400)

def is_all_blank(*args):
    return not all([value for value in args])

def generate_order_number(date_time, max_order_number):
    return datetime.strftime(date_time, '%Y%m%d%H%M%S%f') + \
           str(max_order_number).zfill(10)

class RequiredInputException(Exception):
    def __init__(self):
        super().__init__('MISSING_REQUIRED_INPUT_FIELD')

class PermanentProductException(Exception):
    def __init__(self):
        super().__init__('PERMANENT_PRODUCT')

class AlreadyOwnedProductException(Exception):
    def __init__(self):
        super().__init__('ALREADY_OWNED_PRODUCT')
