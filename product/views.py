import json
from datetime import date, datetime

from django.db.models import Count
from django.views import View
from django.http import JsonResponse

from product.models import Product, Chapter, Lecture, LectureVideo, LectureContent
from user.models import User, ProductLike, RecentlyView, UserProduct
from core.utils import login_decorator
from clnass_101.settings import S3_BUCKET_URL


class ProductDetailView(View):
    
    @login_decorator(login_required=False)
    def get(self, request, product_id):
        try:
            if not isinstance(product_id, int):
                raise TypeError
            
            product = Product.objects. \
                select_related(
                    'sub_category',
                    'difficulty',
                    'creator',
                    'signature',
                ).prefetch_related(
                    'productsubimage_set',
                    'chapter_set',
                    'community_set',
                    'productlike_set',
                    'productkit_set',
                ).get(id=product_id, is_deleted=0)
            
            product_sub_images = [
                {
                    'imageUrl': sub_image['image_url']
                } for sub_image in product.productsubimage_set.all().values('image_url')
            ]
            
            chapters = product.chapter_set.all(). \
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
                    user_id=request.user.id,
                    product_id=product_id
                ).exists()
                
                if not RecentlyView.objects.filter(
                    user_id=request.user.id,
                    product_id=product.id
                ).exists():
                    RecentlyView.objects.create(
                        user_id=request.user.id,
                        product_id=product_id
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
                'curriculum' : [
                    {
                        'thumbnailImage' : chapter.thumbnail_image,
                        'chapterName'    : chapter.name,
                        'order'          : chapter.order,
                        'chapterDetail'  : [
                            {
                                'lectureNum'      : index + 1,
                                'lectureTitle'    : lecture.name,
                                'lectureVideoUrl' : lecture.video.video_url,
                            } for index, lecture in enumerate(chapter.lecture_set.all())
                        ]
                    } for chapter in chapters
                ],
                'kitInfo' : [
                    {
                        'mainImageUrl' : kit.main_image_url,
                        'kitName'      : kit.name,
                        'subImageUrls' : [
                            {
                                'subImageUrl' : sub_image.image_url
                            } for sub_image in kit.kitsubimageurl_set.all()
                        ]
                    } for kit in kits
                ],
                'creatorInfo' : get_user_info(creator_communities[0])
                                    if creator_communities else {},
                'creatorCommunity' : [
                    {
                        'communityUserInfo'      : get_user_info(community),
                        'communityCommentedDate' : community.updated_at.strftime('%Y.%m.%d.'),
                        'comment'                : community.description,
                        'communityId'            : community.id
                    } for community in creator_communities
                ],
                'community' : [
                    {
                        'communityUserInfo'      : get_user_info(community),
                        'communityCommentedDate' : community.updated_at.strftime('%Y.%m.%d.'),
                        'comment'                : community.description,
                        'communityId'            : community.id
                    } for community in communities
                ],
                'classId' : product.id
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


class LectureDetailView(View):
    
    @login_decorator(login_required=False)
    def get(self, request, chapter_id, lecture_id):
        try:
            chapter = Chapter.objects.get(id=chapter_id)
            lecture = Lecture.objects.get(id=lecture_id, chapter_id=chapter_id)
            
            lecture_contents = \
                LectureContent.objects.filter(lecture_id=lecture_id). \
                    select_related(
                        'lecture__video',
                        'image_url',
                        'description'
                    ).order_by('order')
            
            class_detail = {
                'chapter_id'      : chapter.id,
                'class_title'     : chapter.name,
                'lecture_id'      : lecture.id,
                'lecture_title'   : lecture.name,
                'lecture_purpose' : lecture_contents[0].description.description,
                'lecture_url'     : S3_BUCKET_URL + lecture.video.video_url,
                'lecture_detail'  : [
                    {
                        "id"         : content.id,
                        "detail_des" : content.description.description,
                        "image_url"  : S3_BUCKET_URL + content.image_url.image_url,
                        "set_time"   : "1:25"
                    } for content in lecture_contents],
            }
        
        except TypeError:
            return JsonResponse({'MESSAGE': 'TYPE_ERROR'}, status=400)
        
        return JsonResponse({'LECTURE': class_detail}, status=200)


class ClassDetailView(View):
    
    @login_decorator(login_required=True)
    def get(self, request, product_id):
        try:
            if not isinstance(product_id, int):
                raise TypeError
            
            product = Product.objects. \
                prefetch_related('chapter_set', 'lecture_set'). \
                get(id=product_id, is_deleted=0)
            
            purchased_date = UserProduct.objects.get(
                user_id=request.user.id, product_id=product_id).created_at
            
            if product.effective_time:
                
                if product.effective_time + purchased_date < datetime.today():
                    raise ExpiredUsePeriodException
            
            chapters = product.chapter_set.all().order_by('order')
            video_url = chapters[0].lecture_set.all()[0].video.video_url
            
            classData = {
                'thumbnail'  : product.thumbnail_image,
                'title'      : product.name,
                'progress'   : '0',
                'video_url'  : S3_BUCKET_URL + video_url,
                'curriculum' : [
                    {
                        'id'             : chapter.id,
                        'chapter_number' : 'CHAPTER ' + str(chapter.order),
                        'chapter_title'  : chapter.name,
                        'lectures'       : [
                            {
                                'lecture_title' : lecture.name,
                                'lecture_url'   : S3_BUCKET_URL + lecture.video.video_url,
                                'duration'      : '0.00',
                            } for lecture in chapter.lecture_set.all()],
                    } for chapter in chapters]
            }
        
        except TypeError:
            return JsonResponse({'MESSAGE': 'TYPE_ERROR'}, status=400)
        
        except ExpiredUsePeriodException as e:
            return JsonResponse({'MESSAGE': e.__str__()}, status=400)
        
        return JsonResponse({'MESSAGE': classData}, status=200)

def get_user_info(community):
    return User.objects.values(
        'id', 'nick_name', 'profile_image'
    ).get(id=community.user_id)


class ExpiredUsePeriodException(Exception):
    def __init__(self):
        super().__init__('USE_PERIOD_EXPIRED')


class MainPageView(View):
    def get(self, request):
        try:
            sorting = request.GET.get('sorting')
            main_category_id = request.GET.get('main')
            sub_category_id = request.GET.get('sub')
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
            
            sortings = {
                'updated': '-created_at',
                'popular': '-likecount'
            }
            
            if sorting in sortings:
                products = products.order_by(sortings[sorting])
            products_list = [{
                'created_at' : product.created_at,
                'id'         : product.id,
                'title'      : product.name,
                'thumbnail'  : product.thumbnail_image,
                'subCategory': product.sub_category.name,
                'creator'    : product.creator.name,
                'isLiked'    : False,
                'likeCount'  : product.likecount,
                'price'      : int(product.price),
                'sale'       : product.sale,
                'finalPrice' : round(int(product.price * (1 - product.sale)), 2)
            } for product in products.filter(**filters)]
            
            if not products_list:
                return JsonResponse({'MESSAGE': 'NO_RESULT'}, status=400)
        except KeyError as e:
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except TypeError:
            return JsonResponse({'MESSAGE': 'TYPE_ERROR'}, status=400)
        except json.JSONDecodeError as e:
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)
        return JsonResponse({'RESULT': products_list}, status=200)