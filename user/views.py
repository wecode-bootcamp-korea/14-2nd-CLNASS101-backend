import json
import requests
from datetime import datetime, timedelta

from django.db.models import Count, Q
from django.views import View
from django.http import JsonResponse

from my_settings import SECRET, ALGORITHM
from core.utils import login_decorator

from .models import *
from product.models import Product, Community, CommunityLike, CommunityComment, Lecture, LectureComment

from core.utils import (
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
            access_token = request.headers.get("Authorization", None)
            if not access_token:
                return JsonResponse({'MESSAGE': 'TOKEN_REQUIRED'}, status=400)
            url = "https://kapi.kakao.com/v2/user/me"
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            response = requests.get(url, headers=headers).json()
            if not 'email' in response['kakao_account']:
                return JsonResponse({'MESSAGE': 'EMAIL_REQUIRED'}, status=405)
            kakao_user = User.objects.get_or_create(
                name=response["properties"]["nickname"],
                email=response["kakao_account"]["email"],
                profile_image=response["properties"]["profile_image"],
            )[0]
            token = issue_token(kakao_user.id)
            return JsonResponse({"token": token, "name": kakao_user.name, 'profile_image': kakao_user.profile_image},
                                status=200)
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
            search = request.GET.get('search')
            sorting = request.GET.get('sorting')
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
            
            sortings = {
                None     : '-created_at',
                'updated': '-created_at',
                'views'  : products.annotate(viewcount=Count('product_view_user')).order_by('-viewcount'),
                'popular': products.annotate(count=Count('product_like_user')).order_by('-count')
            }
            if sorting:
                if sorting == 'updated':
                    products = products.order_by(sortings[sorting])
                else:
                    products = sortings[sorting]
            
            if search:
                q &= Q(name__icontains=search) | \
                     Q(main_category__name__icontains=search) | \
                     Q(sub_category__name__icontains=search) | \
                     Q(creator__name__icontains=search) | \
                     Q(kit__name__icontains=search) | \
                     Q(detail_category__name__icontains=search)
            
            if not search:
                return JsonResponse({'MESSAGE': 'WRONG_KEY'}, status=400)
            
            search_list = [{
                'id'         : product.id,
                'title'      : product.name,
                'thumbnail'  : product.thumbnail_image,
                'subCategory': product.sub_category.name,
                'creator'    : product.creator.name,
                'isLiked'    : True if ProductLike.objects.filter(product_id=product.id).exists() else False,
                'likeCount'  : product.creator.product_like.all().count(),
                'price'      : int(product.price),
                'sale'       : product.sale,
                'finalPrice' : round(int(product.price * (1 - product.sale)), 2)
            } for product in products.filter(q, **filters)]
            
            if not search_list:
                return JsonResponse({'MESSAGE': 'NO_RESULT'}, status=400)
            return JsonResponse({'search_result': search_list}, status=200)
        except KeyError as e:
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except TypeError:
            return JsonResponse({'MESSAGE': 'TYPE_ERROR'}, status=400)
        except json.JSONDecodeError as e:
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)

class MyPageView(View):
    @login_decorator(login_required=True)
    def get(self, request):
        try:
            user = request.user
            user_object = User.objects.prefetch_related('coupon', 'recently_view__product_like_user',
                                                        'product_like__product_like_user', 'user_product',
                                                        'recently_view__sub_category', 'recently_view__creator',
                                                        'product_like__sub_category', 'product_like__creator').get(
                id=user.id)
            user_profile = {
                'id'          : user_object.id,
                'name'        : user_object.name,
                'profileImage': user_object.profile_image,
                'email'       : user_object.email,
                'point'       : user_object.point,
                'couponNum'   : user_object.coupon.count(),
                'likeNum'     : user_object.product_like.count(),
                'orderNum'    : user_object.user_product.count()
            }
            created_product_list = Product.objects.select_related(
                'creator').filter(creator=user.id)
            #     created_product_list = user_object.filter(creator_id=user.id)
            own_product_list = user_object.user_product.all()
            recently_viewed_list = user_object.recently_view.all()
            like_product_list = user_object.product_like.all()
            created_list = [{
                'classId'   : created.id,
                'title'     : created.name,
                'thumbnail' : created.thumbnail_image,
                'price'     : created.price,
                'sale'      : int(created.sale * 100),
                'finalPrice': round(int(created.price * (1 - created.sale)), 2),
            } for created in created_product_list]
            own_list = [{
                'classId'      : own_product.id,
                'title'        : own_product.name,
                'thumbnail'    : own_product.thumbnail_image,
                'effectiveDate': '평생 수강 쌉가능' if not own_product.effective_time else
                str(((own_product.created_at + own_product.effective_time) -
                     datetime.today() + timedelta(days=1)).days) + '일 남음',
            } for own_product in own_product_list]
            viewed_list = [{
                'classId'    : recent.id,
                'title'      : recent.name,
                'thumbnail'  : recent.thumbnail_image,
                'subCategory': recent.sub_category.name,
                'creator'    : recent.creator.name,
                'isLiked'    : True if recent.filter(product_id=user.recently_view.product.id).exists() else False,
                'likeCount'  : recent.product_like_user.all().count(),
                'price'      : recent.price,
                'sale'       : int((recent.sale) * 100),
                'finalPrice' : round(int(recent.price * (1 - recent.sale)), 2),
            } for recent in recently_viewed_list]
            liked_list = [{
                'classId'    : like_product.id,
                'title'      : like_product.name,
                'thumbnail'  : like_product.thumbnail_image,
                'subCategory': like_product.sub_category.name,
                'creator'    : like_product.creator.name,
                'isLiked'    : True if like_product else False,
                'likeCount'  : like_product.product_like_user.all().count(),
                'price'      : like_product.price,
                'sale'       : int((like_product.sale) * 100),
                'finalPrice' : round(int(like_product.price * (1 - like_product.sale)), 2),
            } for like_product in like_product_list]
            return JsonResponse(
                {'PROFILE': user_profile, 'OWN_PRODUCT': own_list, 'RECENT_VIEW': viewed_list, 'CREATED': created_list,
                 'LIKED'  : liked_list}, status=200)
        except User.DoesNotExist:
            return JsonResponse({'MESSAGE': 'INVALID_USER'}, status=400)
        except Product.DoesNotExist:
            return JsonResponse({'MESSAGE': 'INVALID_PRODUCT'}, status=400)
        except RecentlyView.DoesNotExist:
            return JsonResponse({'MESSAGE': 'INVALID_OBJECT'}, status=400)
        except KeyError as e:
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except json.JSONDecodeError as e:
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)

class CommunityView(View):
    @login_decorator(login_required=True)
    def post(self, request):
        data = json.loads(request.body)
        try:
            user = request.user
            product = Product.objects.get(pk=data['product_id'])
            description = data['description']
            
            Community.objects.create(
                user=user,
                product=product,
                description=description,
            )
            return JsonResponse({'MESSAGE': 'SUCCESS'}, status=200)
        except User.DoesNotExist:
            return JsonResponse({'MESSAGE': 'INVALID_USER'}, status=400)
        except Product.DoesNotExist:
            return JsonResponse({'MESSAGE': 'INVALID_PRODUCT'}, status=400)
        except KeyError as e:
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except json.JSONDecodeError as e:
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)
    
    @login_decorator(login_required=True)
    def patch(self, request, id):
        try:
            user_id = request.user.id
            data = json.loads(request.body)
            description = data['description']
            
            community_update = Community.objects.get(pk=id)
            
            if community_update.user.id is not user_id:
                return JsonResponse({'MESSAGE': 'INVALID_USER'}, status=403)
            community_update.description = description
            community_update.save()
            return JsonResponse({'MESSAGE': 'SUCCESS'}, status=200)
        except Community.DoesNotExist:
            return JsonResponse({'MESSAGE': 'NO_EXIST_COMMUNITY'}, status=400)
        except KeyError as e:
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except json.JSONDecodeError as e:
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)
    
    @login_decorator(login_required=True)
    def delete(self, request, id):
        try:
            user_id = request.user.id
            community_delete = Community.objects.get(pk=id)
            
            if community_delete.user.id is not user_id:
                return JsonResponse({'MESSAGE': 'INVALID_USER'}, status=403)
            community_delete.delete()
            return JsonResponse({'MESSAGE': 'SUCCESS'}, status=200)
        except Community.DoesNotExist:
            return JsonResponse({'MESSAGE': 'NO_EXIST_COMMUNITY'}, status=400)
        except KeyError as e:
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except json.JSONDecodeError as e:
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)
    
    @login_decorator(login_required=True)
    def get(self, request, id):
        try:
            community = Community.objects.select_related('user', 'product', 'product__sub_category',
                                                         'product__creator').prefetch_related(
                'user__community_like', 'user__community_like').get(pk=id)
            comments = community.communitycomment_set.select_related('user').all()
            comment_count = comments.count()
            community_like = community.communitylike_set.all()
            
            community_detail = {
                'id'          : community.id,
                'name'        : community.user.name,
                'profileImage': community.user.profile_image,
                'createdAt'   : community.created_at,
                'content'     : community.description,
                'likeCount'   : community.user.community_like.all().count(),
                'isLiked'     : get_is_like(request.user.id) if request.user else False,
                'commentCount': comment_count,
                'thumbnail'   : community.product.thumbnail_image,
                'subCategory' : community.product.sub_category.name,
                'creator'     : community.product.creator.name,
                'productTitle': community.product.name,
            }
            
            comment_list = [{
                'id'          : comment.id,
                'name'        : comment.user.name,
                'profileImage': comment.user.profile_image,
                'created_at'  : comment.created_at,
                'content'     : comment.content
            } for comment in comments]
            
            return JsonResponse({"community_detail": community_detail, "comment_count": comment_count,
                                 "comment_list"    : comment_list}, status=200)
        except Community.DoesNotExist:
            return JsonResponse({'MESSAGE': 'NO_EXIST_COMMUNITY'}, status=400)
        except KeyError as e:
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except json.JSONDecodeError as e:
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)

def get_is_like(user_id):
    return CommunityLike.objects.filter(community_id=id, user_id=user_id).exists()

class CommunityCommentView(View):
    @login_decorator(login_required=True)
    def post(self, request):
        data = json.loads(request.body)
        try:
            user = request.user
            content = data['content']
            
            CommunityComment.objects.create(
                user=user,
                communtiy_id=data['community_id'],
                content=content,
            )
            return JsonResponse({'MESSAGE': 'SUCCESS'}, status=200)
        except User.DoesNotExist:
            return JsonResponse({'MESSAGE': 'INVALID_USER'}, status=400)
        except Community.DoesNotExist:
            return JsonResponse({'MESSAGE': 'INVALID_COMMUNITY'}, status=400)
        except CommunityComment.DoesNotExist:
            return JsonResponse({'MESSAGE': 'INVALID_COMMENT'}, status=400)
        except KeyError as e:
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except json.JSONDecodeError as e:
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)
    
    @login_decorator(login_required=True)
    def delete(self, request, id):
        user_id = request.user.id
        try:
            community_comment_delete = CommunityComment.objects.get(pk=id)
            if community_comment_delete.user.id is not user_id:
                return JsonResponse({'MESSAGE': 'INVALID_USER'}, status=403)
            community_comment_delete.delete()
            return JsonResponse({'MESSAGE': 'SUCCESS'}, status=200)
        except CommunityComment.DoesNotExist:
            return JsonResponse({'MESSAGE': 'NO_EXIST_COMMUNITY'}, status=400)
        except KeyError as e:
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except json.JSONDecodeError as e:
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)

class LectureCommentView(View):
    @login_decorator(login_required=True)
    def post(self, request):
        data = json.loads(request.body)
        try:
            user = request.user
            lecture = Lecture.objects.get(pk=data['lecture_id'])
            content = data['content']
            image_url = data['image_url']
            
            LectureComment.objects.create(
                user=user,
                lecture=lecture,
                content=content,
                image_url=image_url
            )
            return JsonResponse({'MESSAGE': 'SUCCESS'}, status=200)
        except User.DoesNotExist:
            return JsonResponse({'MESSAGE': 'INVALID_USER'}, status=400)
        except Lecture.DoesNotExist:
            return JsonResponse({'MESSAGE': 'INVALID_LECTURE'}, status=400)
        except KeyError as e:
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except json.JSONDecodeError as e:
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)
    
    @login_decorator(login_required=True)
    def patch(self, request, id):
        data = json.loads(request.body)
        try:
            user_id = request.user.id
            content = data['content']
            lecture_comment_update = LectureComment.objects.get(pk=id)
            
            if lecture_comment_update.user.id != user_id:  # 수정하기 누르자마자 작성자 아니면 걸러지는
                return JsonResponse({'MESSAGE': 'INVALID_USER'}, status=403)
            lecture_comment_update.content = content
            lecture_comment_update.save()
            return JsonResponse({'MESSAGE': 'SUCCESS'}, status=200)
        except LectureComment.DoesNotExist:
            return JsonResponse({'MESSAGE': 'NO_EXIST_COMMENT'}, status=400)
        except KeyError as e:
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except json.JSONDecodeError as e:
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)
    
    @login_decorator(login_required=True)
    def delete(self, request, id):
        user_id = request.user.id
        try:
            lecture_comment_delete = LectureComment.objects.get(pk=id)
            if lecture_comment_delete.user.id != user_id:
                return JsonResponse({'MESSAGE': 'INVALID_USER'}, status=403)
            lecture_comment_delete.delete()
            return JsonResponse({'MESSAGE': 'SUCCESS'}, status=200)
        except LectureComment.DoesNotExist:
            return JsonResponse({'MESSAGE': 'NO_EXIST_COMMENT'}, status=400)
        except KeyError as e:
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except json.JSONDecodeError as e:
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)
    
    @login_decorator(login_required=True)
    def get(self, request):
        try:
            
            lecture_comments = LectureComment.objects.select_related('user').filter(user_id=user_id)
            comment_count = LectureComment.objects.all().count()
            comments = [{
                'id'          : lecture_comment.id,
                'name'        : lecture_comment.user.name,
                'profileImage': lecture_comment.user.profile_image,
                'createdAt'   : lecture_comment.created_at,
                'content'     : lecture_comment.content,
            } for lecture_comment in lecture_comments]
            
            return JsonResponse({"comment_count": comment_count, "comment_list": comments}, status=200)
        except LectureComment.DoesNotExist:
            return JsonResponse({'MESSAGE': 'NO_EXIST_COMMENT'}, status=400)
        except KeyError as e:
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except json.JSONDecodeError as e:
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)

class CommunityLikeView(View):
    @login_decorator(login_required=True)
    def post(self, request):
        try:
            data = json.loads(request.body)
            user_id = request.user.id
            community_id = data['community_id']
            
            if CommunityLike.objects.prefetch_related('community_like_user').filter(user=user_id,
                                                                                    community=community_id).exists():
                CommunityLike.objects.get(user=user_id, community=community_id).delete()
                return JsonResponse({'MESSAGE': 'REMOVED'}, status=200)
            
            CommunityLike(
                user_id=user_id,
                community_id=community_id
            ).save()
            return JsonResponse({'MESSAGE': 'LIKED_COMMUNITY'}, status=201)
        except KeyError as e:
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except json.JSONDecodeError as e:
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)

class ProductLikeView(View):
    @login_decorator(login_required=True)
    def post(self, request):
        try:
            data = json.loads(request.body)
            user_id = request.user.id
            product_id = data['product_id']
            
            if ProductLike.objects.prefetch_related('product_like_user').filter(user=user_id,
                                                                                product=product_id).exists():
                ProductLike.objects.get(user=user_id, product=product_id).delete()
                return JsonResponse({'MESSAGE': 'REMOVED'}, status=200)
            
            ProductLike(
                user_id=user_id,
                product_id=data['product_id']
            ).save()
            return JsonResponse({'MESSAGE': 'LIKED_PRODUCT'}, status=201)
        except KeyError as e:
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except json.JSONDecodeError as e:
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)