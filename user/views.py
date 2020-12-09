import json
import requests
from datetime import datetime, timedelta

from django.views import View
from django.http import JsonResponse

from my_settings import SECRET, ALGORITHM
from .models import User, RecentlyView, ProductLike, UserProduct
from product.models import Product
from core.utils import (
    get_hashed_pw,
    is_valid_name,
    is_valid_email,
    is_valid_password,
    checkpw,
    issue_token,
    login_decorator
)

class SignUpView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)

            name = data["name"]
            email = data["email"]
            password = data["password"]

            if User.objects.filter(email=email).exists():
                return JsonResponse({"MESSAGE": "DUPLICATE_INFORMATION"}, status=409)

            if not is_valid_name(name):
                return JsonResponse({"MESSAGE": "INVALID_NAME"}, status=400)

            if not is_valid_email(email):
                return JsonResponse({"MESSAGE": "INVALID_EMAIL"}, status=400)

            if not is_valid_password(password):
                return JsonResponse({"MESSAGE": "INVALID_PASSWORD"}, status=400)

            User.objects.create(
                name=name,
                email=email,
                password=get_hashed_pw(password)
            )

            return JsonResponse({"MESSAGE": "SUCCESS"}, status=201)
        except json.JSONDecodeError as e:
            return JsonResponse({"MESSAGE": f"JSON_ERROR:{e}"}, status=400)
        except TypeError:
            return JsonResponse({"MESSAGE": "TYPE_ERROR"}, status=400)
        except KeyError as e:
            return JsonResponse({"MESSAGE": f"KEY_ERROR:{e}"}, status=400)

class LogInView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            user = User.objects.get(email=data["email"])
            password = data["password"]

            if not checkpw(password, user):
                return JsonResponse({"MESSAGE": "INVALID_PASSWORD"}, status=401)

            token = issue_token(user.id)

            return JsonResponse({"token": token, "name": user.name}, status=200)

        except User.DoesNotExist:
            return JsonResponse({"MESSAGE": "NO_EXIST_USER"}, status=401)
        except json.JSONDecodeError as e:
            return JsonResponse({"MESSAGE": f"JSON_ERROR:{e}"}, status=400)
        except TypeError:
            return JsonResponse({"MESSAGE": "TYPE_ERROR"}, status=400)
        except KeyError as e:
            return JsonResponse({"MESSAGE": f"KEY_ERROR:{e}"}, status=400)

class KakaoLogInView(View):
    def post(self, request):
        try:
            access_token = request.headers["Authorization"]

            if not access_token:
                return JsonResponse({'MESSAGE': 'TOKEN_REQUIRED'}, status=400)

            url = "https://kapi.kakao.com/v2/user/me"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-type": "application/x-www-form-urlencoded; charset=utf-8",
            }
            response = requests.get(url, headers=headers)
            kakao_user = json.loads(response)

            if not 'email' in kakao_user['kakao_account']:
                return JsonResponse({'MESSAGE': 'EMAIL_REQUIRED'}, status=405)

            kakao_user = User.objects.get_or_create(
                kakao_id=kakao_user["id"],
                name=kakao_user["properties"]["nickname"],
                email=kakao_user["kakao_account"]["email"],
                profile_image=kakao_user["properties"]["profile_image"],
            )[0]

            token = issue_token(kakao_user.id)

            return JsonResponse({"token": token, "name": kakao_user.name, "id": kakao_user.id}, status=200)
        except json.JSONDecodeError as e:
            return JsonResponse({"MESSAGE": f"JSON_ERROR:{e}"}, status=400)
        except User.DoesNotExist:
            return JsonResponse({"MESSAGE": "NO_EXIST_USER"}, status=401)
        except TypeError:
            return JsonResponse({"MESSAGE": "TYPE_ERROR"}, status=400)
        except KeyError as e:
            return JsonResponse({"MESSAGE": f"KEY_ERROR:{e}"}, status=400)

class MyPageView(View):
    @login_decorator
    def get(self,request):
        try:
            user = request.user

            profile = User.objects.prefetch_related('coupon','product_like').get(pk=user.id)

            user_profile = {
                'id': profile.id,
                'name': profile.name,
                'profileImage': profile.profile_image,
                'email': profile.email,
                'point': profile.point,
                'couponNum': profile.coupon.count(),
                'likeNum': profile.product_like.count(),
                'orderNum':profile.user_product.count()
            }

            recently_viewed_list = RecentlyView.objects.select_related('product','product__creator','product__sub_category','user').prefetch_related('user__product_like').filter(user_id=user.id)
            like_product_list    = ProductLike.objects.select_related('product','product__creator','product__sub_category').filter(user_id=user.id)
            own_product_list     = UserProduct.objects.select_related('product').filter(user_id=user.id)
            created_product_list = Product.objects.select_related('creator').filter(creator=user.id)

            created_list = [{
                'classId'     : created.id,
                'title'       : created.name,
                'thumbnail'   : created.thumbnail_image,
                'price'       : created.price,
                'sale'        : int(created.sale*100),
                'finalPrice'  : round(int(created.price * (1-created.sale)),2),
            } for created in created_product_list]

            own_list = [{
                'classId'       : own_product.product.id,
                'title'         : own_product.product.name,
                'thumbnail'     : own_product.product.thumbnail_image,
                'effectiveDate' : '평생 수강 쌉가능' if not own_product.product.effective_time else
                str(((own_product.created_at + own_product.product.effective_time) - datetime.today() + timedelta(days=1)).days) + '일 남음',
                } for own_product in own_product_list]

            viewed_list = [{
                'classId'     : recently_viewed.product.id,
                'title'       : recently_viewed.product.name,
                'thumbnail'   : recently_viewed.product.thumbnail_image,
                'subCategory' : recently_viewed.product.sub_category.name,
                'creator'     : recently_viewed.product.creator.name,
                'isLiked'     : True if like_product_list.filter(product_id=recently_viewed.product.id).exists() else False,
                'likeCount'   : recently_viewed.product.product_like_user.all().count(),
                'price'       : recently_viewed.product.price,
                'sale'        : int((recently_viewed.product.sale)*100),
                'finalPrice'  : round(int(recently_viewed.product.price * (1-recently_viewed.product.sale)),2),
                } for recently_viewed in recently_viewed_list]

            liked_list = [{
                'classId'     : like_product.product.id,
                'title'       : like_product.product.name,
                'thumbnail'   : like_product.product.thumbnail_image,
                'subCategory' : like_product.product.sub_category.name,
                'creator'     : like_product.product.creator.name,
                'isLiked'     : True if like_product else False,
                'likeCount'   : like_product.product.product_like_user.all().count(),
                'price'       : like_product.product.price,
                'sale'        : int((like_product.product.sale)*100),
                'finalPrice'  : round(int(like_product.product.price * (1-like_product.product.sale)),2),
                } for like_product in like_product_list]

            return JsonResponse({'PROFILE':user_profile, 'OWN_PRODUCT':own_list, 'RECENT_VIEW':viewed_list, 'CREATED':created_list, 'LIKED':liked_list}, status=200)
        except User.DoesNotExist:
            return JsonResponse({'MESSAGE':'INVALID_USER'}, status=400)
        except Product.DoesNotExist:
            return JsonResponse({'MESSAGE':'INVALID_PRODUCT'}, status=400)
        except RecentlyView.DoesNotExist:
            return JsonResponse({'MESSAGE':'INVALID_OBJECT'}, status=400)
        except KeyError as e :
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except json.JSONDecodeError as e :
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)


            return JsonResponse({'PROFILE':user_profile, 'OWN_PRODUCT':own_list, 'RECENT_VIEW':viewed_list, 'CREATED':created_list, 'LIKED':liked_list}, status=200)