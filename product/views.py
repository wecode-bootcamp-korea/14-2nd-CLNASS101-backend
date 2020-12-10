import json
from datetime       import date

from django.views   import View
from django.http    import JsonResponse

from product.models import Product, Community, CommunityComment, CommunityLike, Lecture, LectureComment
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

class CommunityView(View):
    @login_decorator(view_name='CommunityView')
    def post(self, request):
        data=json.loads(request.body)
        try:
            user        = request.user
            product     = Product.objects.get(pk=data['product_id'])
            description = data['description']

            Community.objects.create(
                user        = user,
                product     = product,
                description = description,
            )
            return JsonResponse({'MESSAGE':'SUCCESS'}, status=200)
        except User.DoesNotExist:
            return JsonResponse({'MESSAGE':'INVALID_USER'}, status=400)
        except Product.DoesNotExist:
            return JsonResponse({'MESSAGE':'INVALID_PRODUCT'}, status=400)
        except KeyError as e :
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except json.JSONDecodeError as e :
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)
    
    @login_decorator(view_name='CommunityView')
    def patch(self, request, id):
        try:
            user_id     = request.user.id
            data        = json.loads(request.body)
            description = data['description']

            community_update = Community.objects.get(pk=id)

            if community_update.user.id is not user_id: 
                return JsonResponse({'MESSAGE':'INVALID_USER'}, status=403)
            community_update.description = description
            community_update.save()
            return JsonResponse({'MESSAGE':'SUCCESS'}, status=200)
        except Community.DoesNotExist:
            return JsonResponse({'MESSAGE':'NO_EXIST_COMMUNITY'}, status=400)
        except KeyError as e :
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except json.JSONDecodeError as e :
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)

    @login_decorator(view_name='CommunityView')
    def delete(self, request, id):
        try:
            user_id          = request.user.id
            community_delete = Community.objects.get(pk=id)
            
            if community_delete.user.id is not user_id: 
                return JsonResponse({'MESSAGE':'INVALID_USER'}, status=403)
            community_delete.delete()
            return JsonResponse({'MESSAGE':'SUCCESS'}, status=200)
        except Community.DoesNotExist:
            return JsonResponse({'MESSAGE':'NO_EXIST_COMMUNITY'}, status=400)
        except KeyError as e :
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except json.JSONDecodeError as e :
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)

    @login_decorator(view_name='CommunityView')
    def get(self, request, id):
        try:
            community      = Community.objects.select_related('user','product','product__sub_category','product__creator').prefetch_related('user__community_like','user__community_like').get(pk=id)
            comments       = CommunityComment.objects.select_related('user').filter(community_id=id)
            comment_count  = CommunityComment.objects.filter(community_id=id).count()
            community_like = CommunityLike.objects.filter(community_id=id)

            community_detail = {
                'id'           : community.id,
                'name'         : community.user.name,
                'profileImage' : community.user.profile_image,
                'createdAt'    : community.created_at,
                'content'      : community.description,
                'likeCount'    : community.user.community_like.all().count(),
                'isLiked'      : get_is_like(request.user.id) if request.user else False,
                'commentCount' : comment_count,
                'thumbnail'    : community.product.thumbnail_image,
                'subCategory'  : community.product.sub_category.name,
                'creator'      : community.product.creator.name,
                'productTitle' : community.product.name,
                }

            comment_list = [{
                'id'           : comment.id,
                'name'         : comment.user.name,
                'profileImage' : comment.user.profile_image,
                'created_at'   : comment.created_at,
                'content'      : comment.content 
                } for comment in comments ]

            return JsonResponse({"community_detail": community_detail, "comment_count": comment_count, "comment_list": comment_list}, status=200)
        except Community.DoesNotExist:
            return JsonResponse({'MESSAGE':'NO_EXIST_COMMUNITY'}, status=400)
        except KeyError as e :
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except json.JSONDecodeError as e :
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)

def get_is_like(user_id):
    return CommunityLike.objects.filter(community_id=id, user_id =user_id).exists()


class CommunityCommentView(View):
    @login_decorator(view_name='CommunityCommentView')
    def post(self, request):
        data=json.loads(request.body)
        try:
            user      = request.user
            community = Community.objects.get(pk=data['community_id'])
           # comment   = CommunityComment.objects.get(pk=data['community_comment_id'])
            content   = data['content']

            CommunityComment.objects.create(
                user      = user,
                communtiy = community,
                content   = content,
            )
            return JsonResponse({'MESSAGE':'SUCCESS'}, status=200)
        except User.DoesNotExist:
            return JsonResponse({'MESSAGE':'INVALID_USER'}, status=400)
        except Community.DoesNotExist:
            return JsonResponse({'MESSAGE':'INVALID_COMMUNITY'}, status=400)
        except CommunityComment.DoesNotExist:
            return JsonResponse({'MESSAGE':'INVALID_COMMENT'}, status=400)
        except KeyError as e :
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except json.JSONDecodeError as e :
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)
#커뮤니티 댓글 지우기
    @login_decorator
    def delete(self, request, id):
        user_id = request.user.id
        try:
            community_comment_delete = CommunityComment.objects.get(pk=id)
            if community_comment_delete.user.id is not user_id: 
                return JsonResponse({'MESSAGE':'INVALID_USER'}, status=403)
            community_comment_delete.delete()
            return JsonResponse({'MESSAGE':'SUCCESS'}, status=200)
        except CommunityComment.DoesNotExist:
            return JsonResponse({'MESSAGE':'NO_EXIST_COMMUNITY'}, status=400)
        except KeyError as e :
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except json.JSONDecodeError as e :
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)

class LectureCommentView(View):
    @login_decorator(view_name='LectureCommentView')
    def post(self, request):
        data=json.loads(request.body)
        try:
            user        = request.user
            lecture     = Lecture.objects.get(pk=data['lecture_id'])
            content     = data['content'] 
            image_url   = data['image_url']

            LectureComment.objects.create(
                user      = user,
                lecture   = lecture,
                content   = content,
                image_url = image_url
            )
            return JsonResponse({'MESSAGE':'SUCCESS'}, status=200)
        except User.DoesNotExist:
            return JsonResponse({'MESSAGE':'INVALID_USER'}, status=400)
        except Lecture.DoesNotExist:
            return JsonResponse({'MESSAGE':'INVALID_LECTURE'}, status=400)
        except KeyError as e :
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except json.JSONDecodeError as e :
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)
    
    @login_decorator(view_name='LectureCommentView')
    def patch(self, request, id):
        data = json.loads(request.body)
        try:
            user_id                = request.user.id
            content                = data['content']
            lecture_comment_update = LectureComment.objects.get(pk=id)

            if lecture_comment_update.user.id != user_id: #수정하기 누르자마자 작성자 아니면 걸러지는
                return JsonResponse({'MESSAGE':'INVALID_USER'}, status=403)
            lecture_comment_update.content = content
            lecture_comment_update.save()
            return JsonResponse({'MESSAGE':'SUCCESS'}, status=200)
        except LectureComment.DoesNotExist:
            return JsonResponse({'MESSAGE':'NO_EXIST_COMMENT'}, status=400)
        except KeyError as e :
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except json.JSONDecodeError as e :
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)

    @login_decorator(view_name='LectureCommentView')
    def delete(self, request, id):
        user_id = request.user.id
        try:
            lecture_comment_delete = LectureComment.objects.get(pk=id)
            if lecture_comment_delete.user.id != user_id: 
                return JsonResponse({'MESSAGE':'INVALID_USER'}, status=403)
            lecture_comment_delete.delete()
            return JsonResponse({'MESSAGE':'SUCCESS'}, status=200)
        except LectureComment.DoesNotExist:
            return JsonResponse({'MESSAGE':'NO_EXIST_COMMENT'}, status=400)
        except KeyError as e :
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except json.JSONDecodeError as e :
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)
    @login_decorator(view_name='LectureCommentView')
    def get(self, request):
        try:

            lecture_comments = LectureComment.objects.select_related('user').filter(user_id=user_id)
            comment_count    = LectureComment.objects.filter(lecture_id=lecture_id).count()
            comments = [{
            'id'           : lecture_comment.id,
            'name'         : lecture_comment.user.name,
            'profileImage' : lecture_comment.user.profile_image,
            'createdAt'    : lecture_comment.created_at,
            'content'      : lecture_comment.content,
            } for lecture_comment in lecture_comments]

            return JsonResponse({"comment_count": comment_count, "comment_list": comments}, status=200)
        except LectureComment.DoesNotExist:
            return JsonResponse({'MESSAGE':'NO_EXIST_COMMENT'}, status=400)
        except KeyError as e :
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except json.JSONDecodeError as e :
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)

class CommunityLikeView(View):
    @login_decorator(view_name='CommunityLikeView')
    def post(self, request):
        try:
            data         = json.loads(request.body)
            user_id      = request.user.id
            community_id = data['community_id']

            if CommunityLike.objects.prefetch_related('community_like_user').filter(user=user_id, community=community_id).exists():
                CommunityLike.objects.get(user=user_id, community=community_id).delete()
                return JsonResponse({'MESSAGE':'REMOVED'}, status = 200)
            
            CommunityLike(
                user_id    = user_id,
                community_id = community_id
            ).save()
            return JsonResponse({'MESSAGE':'LIKED_COMMUNITY'}, status=201)
        except KeyError as e :
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except json.JSONDecodeError as e :
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)


class ProductLikeView(View):
    @login_decorator(view_name='ProductLikeView')
    def post(self, request):
        try:
            data       = json.loads(request.body)
            user_id    = request.user.id
            product_id = data['product_id']

            if ProductLike.objects.prefetch_related('product_like_user').filter(user=user_id, product=product_id).exists():
                ProductLike.objects.get(user=user_id, product=product_id).delete()
                return JsonResponse({'MESSAGE':'REMOVED'}, status = 200)
            
            ProductLike(
                user_id    = user_id,
                product_id = data['product_id']
            ).save()
            return JsonResponse({'MESSAGE':'LIKED_PRODUCT'}, status=201)
        except KeyError as e :
            return JsonResponse({'MESSAGE': f'KEY_ERROR:{e}'}, status=400)
        except json.JSONDecodeError as e :
            return JsonResponse({'MESSAGE': f'JSON_DECODE_ERROR:{e}'}, status=400)
    