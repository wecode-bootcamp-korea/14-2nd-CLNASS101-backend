import json
from datetime       import date

from django.db.models import Count
from django.views   import View
from django.http    import JsonResponse

from product.models import Product
from user.models    import User, ProductLike, RecentlyView
from core.utils     import login_decorator

class ProductDetailView(View):
    
    @login_decorator(view_name='ProductDetailView')
    def get(self, request, product_id):
        try:
            if not isinstance(product_id, int):
                raise TypeError
            
            product = Product.objects.\
                select_related(
                    'sub_category', 'difficulty', 'creator', 'signature',
                ).\
                prefetch_related(
                    'productsubimage_set',
                    'chapter_set',
                    'community_set',
                    'productlike_set',
                    'productkit_set',
                ).get(id=product_id, is_deleted=0)
            
            product_sub_images = [
                {
                    'imageUrl' : sub_image['image_url']
                } for sub_image in product.productsubimage_set.all().values('image_url')
            ]
            
            chapters = product.chapter_set.all().\
                prefetch_related('lecture_set').order_by('order')
            
            kits = [
                product_kits.kit for product_kits in product.productkit_set.all()
            ]
            
            product_communities = product.community_set.all().order_by('-updated_at')
            
            creator_communities = [
                community for community in product_communities
                if community.user_id == product.creator_id
                   or community.user_id == product.signature_id
            ]
            
            communities = [
                community for community in product_communities
            ]
            
            is_like = False
            if request.user:
                is_like = ProductLike.objects.filter(
                    user_id    = request.user.id,
                    product_id = product_id
                ).exists()
                
                if not RecentlyView.objects.filter(
                    user_id    = request.user.id,
                    product_id = product.id
                ).exists():
                    RecentlyView.objects.create(
                        user_id    = request.user.id,
                        product_id = product_id
                    )
            
            product_info = {
                'mainImage'       : product.thumbnail_image,
                'subImages'       : product_sub_images,
                'title'           : product.name,
                'subCategoryName' : product.sub_category.name,
                'classOwner'      : product.creator.nick_name if not product.signature else
                                    product.signature.name,
                'isTakeClass'     : '바로 수강 가능' if product.start_date <= date.today() else
                                    str(product.start_date.month) + '월' + ' ' +
                                    str(product.start_date.day) + '일 부터 수강 가능',
                'sale'            : int(product.sale * 100),
                'price'           : '{:,}원'.format(int(product.price * (1 - product.sale))),
                'difficulty'      : f'{product.difficulty.name} 대상',
                'likeCount'       : product.productlike_set.count(),
                'isLike'          : is_like,
                'curriculum'      : [{
                                        'thumbnail-image' : chapter.thumbnail_image,
                                        'chapter-name'    : chapter.name,
                                        'order'           : chapter.order,
                                        'chapter-detail'  : [{
                                                                'lecture-title'     : lecture.name,
                                                                'lecture-video-url' : lecture.video_url,
                                                            } for lecture in chapter.lecture_set.all()]
                                    } for chapter in chapters],
                'kitInfo'         : [{
                                        'mainImageUrl'    : kit.main_image_url,
                                        'description'     : kit.description,
                                        'subImageUrls'    : [{
                                                                'subImageUrl' : sub_image.image_url
                                                            } for sub_image in kit.kitsubimageurl_set.all()]
                                    } for kit in kits],
                'creatorInfo'     : get_user_info(creator_communities[0])
                                    if creator_communities else {},
                'creatorCommunity': [{
                                        'communityUserInfo'      : get_user_info(community),
                                        'communityCommentedDate' : community.updated_at.strftime('%Y.%m.%d.'),
                                        'comment'                : community.description,
                                        'communityId'            : community.id
                                    } for community in creator_communities],
                'community'       : [{
                                        'communityUserInfo'     : get_user_info(community),
                                        'communityCommentedDate': community.updated_at.strftime('%Y.%m.%d.'),
                                        'comment'               : community.description,
                                        'communityId'           : community.id
                                    } for community in communities],
                'classId'         : product.id
            }
        
        except TypeError:
            return JsonResponse({'MESSAGE': 'TYPE_ERROR'}, status=400)
        
        except Product.DoesNotExist:
            return JsonResponse({'MESSAGE': 'PRODUCT_NOT_EXIST'}, status=400)
        
        except User.DoesNotExist:
            return JsonResponse({'MESSAGE': 'USER_NOT_EXIST'}, status=400)
        
        except AttributeError:
            return JsonResponse({'MESSAGE': 'ATTRIBUTE_ERROR'}, status=400)

        return JsonResponse({'CLASS': product_info}, status=200)

def get_user_info(community):
    return User.objects.values(
                'id', 'nick_name', 'profile_image'
           ).get(id=community.user_id)

class MainPageView(View):
    def get(self, request):
        try:
            sorting          = request.GET.get('sorting')
            main_category_id = request.GET.get('main')
            sub_category_id  = request.GET.get('sub')
        
            products = Product.objects.select_related(
                'main_category',
                'sub_category',
                'creator'
                ).prefetch_related(
                    'product_like_user',
                    'product_view_user'
                    ).annotate(likecount=Count('product_like_user'))

            filters = {}

            if main_category_id:
                filters['main_category__id'] = main_category_id

            if sub_category_id:
                filters['sub_category__id'] = sub_category_id

            sortings   = {
                'updated' : '-created_at',
                'popular' : '-likecount'
            }

            if sorting in sortings:
                products = products.order_by(sortings[sorting])

            products_list = [{
                'created_at'  : product.created_at,
                'id'          : product.id,
                'title'       : product.name,
                'thumbnail'   : product.thumbnail_image,
                'subCategory' : product.sub_category.name,
                'creator'     : product.creator.name,
                'isLiked'     : False, #True if product.product_like_user.exists() else False, 
                #모르겠습니다..새로운 로그인 데코레이터도 적용해야하는데.. 그래야 이게 말이 되는데,, 지금은 로그인 안해서, 좋아요를 못하는 상황...
                'likeCount'   : product.likecount,
                'price'       : int(product.price),
                'sale'        : product.sale,
                'finalPrice'  : round(int(product.price * (1-product.sale)),2)
            } for product in products.filter(**filters)]

            if not products_list:
                return JsonResponse({'MESSAGE': 'NO_RESULT'}, status=400)
        except KeyError as e :
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except TypeError:
            return JsonResponse({'MESSAGE': 'TYPE_ERROR'}, status=400)
        except json.JSONDecodeError as e :
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)
        return JsonResponse({'RESULT': products_list}, status=200)
