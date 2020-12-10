import json
import requests

from django.views     import View
from django.http      import JsonResponse
from django.db.models import Count, Q

from my_settings    import SECRET, ALGORITHM
from .models        import User, ProductLike
from product.models import Product
from core.utils     import (
                            get_hashed_pw,
                            is_valid_name,
                            is_valid_email,
                            is_valid_password,
                            checkpw,
                            issue_token,
                            )

class SignUpView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)

            name     = data["name"]
            email    = data["email"]
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
                name     = name,
                email    = email,
                password = get_hashed_pw(password)
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
            data     = json.loads(request.body)
            user     = User.objects.get(email=data["email"])
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
            access_token = request.headers.get("Authorization", None)
            
            if not access_token:
                return JsonResponse({'MESSAGE': 'TOKEN_REQUIRED'}, status=400)
            
            url     = "https://kapi.kakao.com/v2/user/me"
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            response   = requests.get(url, headers=headers).json()
            
            if not 'email' in response['kakao_account']:
                return JsonResponse({'MESSAGE': 'EMAIL_REQUIRED'}, status=405)
            
            kakao_user = User.objects.get_or_create(
                name=response["properties"]["nickname"],
                email=response["kakao_account"]["email"],
                profile_image=response["properties"]["profile_image"],
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

class SearchView(View):
    def get(self, request):
        try:
            search          = request.GET.get('search')
            sorting         = request.GET.get('sorting')
            sub_category_id = request.GET.get('sub_category')
            
            products = Product.objects.select_related(
                'main_category',
                'sub_category',
                'creator'
                ).prefetch_related(
                    'kit', 
                    'detail_category',
                    'product_like_user',
                    'product_view_user'
                    )

            filters = {}

            if sub_category_id:
                filters['sub_category__name'] = sub_category_id

            q = Q()

            sortings   = {
                None      : '-created_at',
                'updated' : '-created_at',
                'views'   : products.annotate(viewcount=Count('product_view_user')).order_by('-viewcount'),
                'popular' : products.annotate(count=Count('product_like_user')).order_by('-count')
            }
            if sorting:
                if sorting == 'updated':
                    products = products.order_by(sortings[sorting])
                else:
                    products = sortings[sorting]

            if search:
                q &= Q(name__icontains                  = search) |\
                     Q(main_category__name__icontains   = search) |\
                     Q(sub_category__name__icontains    = search) |\
                     Q(creator__name__icontains         = search) |\
                     Q(kit__name__icontains             = search) |\
                     Q(detail_category__name__icontains = search)

            if not search:
                return JsonResponse({'MESSAGE': 'WRONG_KEY'}, status=400)
                
            search_list = [{
                'id'          : product.id,
                'title'       : product.name,
                'thumbnail'   : product.thumbnail_image,
                'subCategory' : product.sub_category.name,
                'creator'     : product.creator.name,
                'isLiked'     : True if ProductLike.objects.filter(product_id=product.id).exists() else False,
                'likeCount'   : product.creator.product_like.all().count(),
                'price'       : int(product.price),
                'sale'        : product.sale,
                'finalPrice'  : round(int(product.price * (1-product.sale)),2)
            } for product in products.filter(q, **filters)]

            if not search_list:
                return JsonResponse({'MESSAGE': 'NO_RESULT'}, status=400)
            return JsonResponse({'search_result': search_list}, status=200)
        except KeyError as e :
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except TypeError:
            return JsonResponse({'MESSAGE': 'TYPE_ERROR'}, status=400)
        except json.JSONDecodeError as e :
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)
