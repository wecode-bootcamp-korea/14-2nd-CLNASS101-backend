import json

from django.http         import JsonResponse
from django.views        import View
from django.db           import transaction
from django.db.models    import Q
from django.utils        import timezone

from creator.models      import (
                            TemporaryProduct,
                            TemporaryProductImage,
                            TemporaryChapter,
                            TemporaryLecture,
                            TemporaryLectureContent,
                            TemporaryLectureContentDescription,
                            TemporaryLectureContentImage,
                            TemporaryKit,
                            TemporaryKitImage
                        )    
from product.models      import ( 
                            MainCategory,
                            SubCategory,
                            Difficulty,
                            LectureContent,
                            LectureContentDescription,
                            LectureContentImageUrl,
                            ProductSubImage,
                            Chapter,
                            Lecture,
                            Product,
                            LectureVideo
                        )
from kit.models          import Kit, KitSubImageUrl
from core                import S3FileManager, random_number_generator
from core.utils          import login_decorator
from clnass_101.settings import S3_BUCKET_URL

class FirstTemporaryView(View):
    @login_decorator('FirstTemporaryView')
    def get(self, request, temporary_id):
        user       = request.user 
        categories = MainCategory.objects.filter(
            Q(name='크리에이티브') |
            Q(name='커리어') |
            Q(name='머니')).prefetch_related('subcategory_set')
        
        category_list = [{
            'id'   :category.id,
            'name' :category.name,
            'subCategories' : [{
                'id'  : sub.id, 
                'name': sub.name
            } for sub in category.subcategory_set.all()]
        } for category in categories]
       
        if TemporaryProduct.objects.filter(id=temporary_id, user=user).exists():
            temp      = TemporaryProduct.objects.prefetch_related('temporaryproductimage_set').get(id=temporary_id, user=user)
            temp_info = {
                'mainCategoryId' : temp.main_category_id,
                'subCategoryId'  : temp.sub_category_id,
                'difficultyId'   : temp.difficulty_id,
                'name'           : temp.name,
                'price'          : temp.price,
                'sale'           : temp.sale,
                'images'         : [S3_BUCKET_URL + image.image_url for image in temp.temporaryproductimage_set.all()]
            }
        else:
            temp_info = None

        return JsonResponse({
            'categories'   : category_list,
            'difficulties' : [difficulty for difficulty in Difficulty.objects.values()],
            'temporaryInformation' : temp_info}, status=200)
    
    @login_decorator('FirstTemporaryView')
    @transaction.atomic
    def post(self, request, temporary_id):
        data   = json.loads(request.POST['body'])
        user   = request.user
        images = request.FILES.getlist('files') 

        required_key = {
            'categoryName',
            'subCategoryName',
            'difficultyName',
            'name',
            'price',
            'sale'
        }
         
        for key in required_key:
            if key not in data:
                return JsonResponse({'message':'KEY_ERROR'}, status=400)
        
        #프론트측의 요청으로 아이디가 아닌 name으로 판별
        category     = MainCategory.objects.get(name=data['categoryName'])
        sub_category = SubCategory.objects.get(name=data['subCategoryName'])
        difficulty   = Difficulty.objects.get(name=data['difficultyName'])

        temp = TemporaryProduct.objects.update_or_create(
            id              = temporary_id,
            user            = user,
            defaults        = {
                'main_category' : category,
                'sub_category'  : sub_category,
                'name'          : data['name'],
                'price'         : data['price'],
                'sale'          : data['sale'],
                'difficulty'    : difficulty
            }
        )[0]
        
        #기존 이미지 삭제
        exist_images = TemporaryProductImage.objects.filter(temporary_product=temp)
        for image in exist_images:
            url = image.image_url
            S3FileManager().file_delete(url)
            image.delete()
         
        #이미지 삽입
        for image in images:
            file_name = 'images/' + random_number_generator()
            url = S3FileManager().file_upload(image, file_name)
            TemporaryProductImage.objects.create(
                temporary_product = temp,
                image_url         = url
            )
            
        return JsonResponse({'message':'SUCCESS'}, status=200)

class SecondTemporaryView(View):
    @login_decorator('SecondTemporaryView')
    def get(self, request, temporary_id):
        chapters = TemporaryChapter.objects.filter(temporary_product_id=temporary_id).prefetch_related('temporarylecture_set')
        
        return JsonResponse({
            'chapters' : [{
                'chapterId'      : chapter.id,
                'name'           : chapter.name,
                'mainImage'      : S3_BUCKET_URL + chapter.thumbnail_image if chapter.thumbnail_image else None,
                'lectures'       : [{
                    'name' : lecture.name
                } for lecture in chapter.temporarylecture_set.all()]
            } for chapter in chapters]
        }, status=200)
    
    @login_decorator('SecondTemporaryView')
    @transaction.atomic
    def post(self, request, temporary_id):
        data = json.loads(request.POST['body'])
        images = request.FILES.getlist('files')
        try:
            chapters = data['chapters']
            
            temps = TemporaryChapter.objects.filter(temporary_product_id=temporary_id)
            for temp in temps:
                #기존 이미지 삭제
                if temp.thumbnail_image:
                    url = temp.thumbnail_image
                    S3FileManager().file_delete(url)
                temp.delete()

            lectures = []
            for i, chapter in enumerate(chapters, start=1):
                temp = TemporaryChapter.objects.create(
                    temporary_product_id = temporary_id,
                    order                = i,
                    name                 = chapter['name'] 
                )
                
                if images:
                    image = images.pop(0)
                    file_name = 'images/' + random_number_generator()
                    url       = S3FileManager().file_upload(image, file_name)
                    temp.thumbnail_image = url 
                    temp.save()
                
                lectures += [{
                    'name'       : lecture.get('name'),
                    'chapter'    : temp.name,
                    'chapter_id' : temp.id
                } for lecture in chapter['lectures']]
            
            order        = 1
            lecture_name = None
            for lecture in lectures:
                if lecture['name'] != lecture_name:
                    order = 1
                lecture_name = lecture['name']

                TemporaryLecture.objects.create(
                    temporary_product_id = temporary_id,
                    temporary_chapter_id = lecture['chapter_id'],
                    order                = order,
                    name                 = lecture['name']
                )
                order += 1

            return JsonResponse({'message':'SUCCESS'}, status=200)

        except KeyError:
            return JsonResponse({'message':'KEY_ERROR'}, status=400)

class ThirdTemporaryView(View):
    @login_decorator('ThirdTemporaryView')
    def get(self, request, temporary_id):
        chapters = TemporaryChapter.objects.filter(temporary_product_id=temporary_id).prefetch_related(
            'temporarylecture_set__temporarylecturecontent_set',
            'temporarylecture_set__temporarylecturecontent_set__image',
            'temporarylecture_set__temporarylecturecontent_set__description'
        )

        return JsonResponse({
            'products' : [{
                'chapter_id'    : chapter.id,
                'chapterName'   : chapter.name,
                'chapterOrder'  : chapter.order,
                'lectures'      : [{
                    'lecture_id' : lecture.id,
                    'name'       : lecture.name,
                    'videoUrl'   : S3_BUCKET_URL + lecture.video_url if lecture.video_url else None,
                    'duration'   : lecture.duration,
                    'order'      : lecture.order,
                    'content'    : [{
                        'image'       : S3_BUCKET_URL + content.image.image_url if content.image.image_url else None,
                        'description' : content.description.description,
                        'order'       : content.order
                    } for content in lecture.temporarylecturecontent_set.all()]
                } for lecture in chapter.temporarylecture_set.all()]
            } for chapter in chapters]
        })
    
    @login_decorator('ThirdTemporaryView')
    @transaction.atomic
    def post(self, request, temporary_id):
        data = json.loads(request.POST['body'])

        try:
            #기존 이미지 제거
            images = TemporaryLectureContentImage.objects.filter(temporary_product_id=temporary_id)
            for image in images:
                S3FileManager().file_delete(image.image_url)
                image.delete()
                
            #기존 글 제거
            TemporaryLectureContentDescription.objects.filter(temporary_product_id=temporary_id).delete()
                
            #기존 글그림 연결 제거
            TemporaryLectureContent.objects.filter(temporary_product_id=temporary_id).delete()
                
            videos = request.FILES.getlist('videos')
            images = request.FILES.getlist('images')
            for lecture in data['lectures']:
                temp      = TemporaryLecture.objects.get(id=lecture['lecture_id'])
               
                #기존 비디오 제거
                if temp.video_url:
                    url = temp.video_url
                    S3FileManager().file_delete(url)
                
                #비디오 삽입
                if videos:
                    video          = videos.pop(0)
                    file_name      = 'videos/' + random_number_generator()
                    url            = S3FileManager().file_upload(video, file_name)
                    temp.video_url = url
                    temp.save()
            
                for i, content in enumerate(lecture['contents'], start=1):
                    #이미지 생성
                    if images:
                        image     = images.pop(0)
                        file_name = 'images/' + random_number_generator()
                        url       = S3FileManager().file_upload(image, file_name)
                        image     = TemporaryLectureContentImage.objects.create(
                            temporary_lecture    = temp,
                            image_url            = url,
                            temporary_product_id = temporary_id
                        )
                        
                    #글생성
                    description = TemporaryLectureContentDescription.objects.create(
                        temporary_lecture    = temp,
                        description          = content['description'],
                        temporary_product_id = temporary_id
                    )
                    
                    #글 그림 연결
                    TemporaryLectureContent.objects.create(
                        order                = i,
                        image                = image,
                        description          = description,
                        temporary_lecture    = temp,
                        temporary_product_id = temporary_id
                    )
            return JsonResponse({'message':'SUCCESS'},status=200)

        except KeyError:
            return JsonResponse({'message':'KEY_ERROR'}, status=400)

class FourthTemporaryView(View):
    @login_decorator('FourthTemporaryView')
    def get(self, request, temporary_id):
        kits = TemporaryKit.objects.filter(temporary_product_id=temporary_id).prefetch_related('temporarykitimage_set')

        return JsonResponse({
                'kits' : [{
                    'id'         : kit.id,
                    'name'       : kit.name,
                    'imageUrls'  : [S3_BUCKET_URL + image.image_url for image in kit.temporarykitimage_set.all()]
                } for kit in kits]
            })

    @login_decorator('FourthTemporaryView')
    @transaction.atomic
    def post(self, request, temporary_id):
        data = json.loads(request.POST['body'])
        images = request.FILES.getlist('files')

        #기존 이미지 삭제
        temp_images = TemporaryKitImage.objects.filter(temporary_kit__temporary_product_id=temporary_id)
        for image in temp_images:
            S3FileManager().file_delete(image.image_url)

        #기존 키트 삭제
        TemporaryKit.objects.filter(temporary_product_id=temporary_id).delete()
        
        #키트 생성
        kits = [kit.get('name') for kit in data['kits']]
        for kit in kits:
            temp = TemporaryKit.objects.create(name=kit, temporary_product_id=temporary_id)

            if images:
                image = images.pop(0)
                file_name = 'images/' + random_number_generator()
                url       = S3FileManager().file_upload(image, file_name)
                TemporaryKitImage.objects.create(image_url=url, temporary_kit=temp, temporary_product_id=temporary_id)

        return JsonResponse({'message':'SUCCESS'}, status=200)

class CreateTemporaryView(View):
    @login_decorator('CreateTemporaryView')
    @transaction.atomic
    def post(self, request, temporary_id):
        user             = request.user
        temp             = TemporaryProduct.objects.prefetch_related(
            'temporaryproductimage_set',
            'temporarylecture_set',
            'temporarylecturecontent_set',
            'temporarykitimage_set'
        ).get(id=temporary_id)

        product_images   = [image for image in temp.temporaryproductimage_set.all()]
        lectures         = [lecture for lecture in temp.temporarylecture_set.all()]
        contents         = [content for content in temp.temporarylecturecontent_set.all()]
        kit_images       = [image for image in temp.temporarykitimage_set.all()]

        #강의 개설
        product = Product.objects.create(
            name            = temp.name, 
            price           = temp.price, 
            sale            = temp.sale,
            difficulty      = temp.difficulty,
            main_category   = temp.main_category,
            sub_category    = temp.sub_category,
            start_date      = timezone.now(),
            creator         = user,
            thumbnail_image = product_images[0].image_url
        )
        
        #sub image
        for image in product_images:
            ProductSubImage.objects.create(product=product, image_url=image.image_url)

        #lecture
        for lecture in lectures:
            if Chapter.objects.filter(name=lecture.temporary_chapter.name, product=product).exists():
                chapter       = Chapter.objects.get(name=lecture.temporary_chapter.name, product=product)
                lecture_video = LectureVideo.objects.create(video_url=lecture.video_url)
                Lecture.objects.create(name=lecture.name, product=product, chapter=chapter, order=lecture.order, video=lecture_video)
            else:
                new_chapter = Chapter.objects.create(
                    name            = lecture.temporary_chapter.name,
                    thumbnail_image = lecture.temporary_chapter.thumbnail_image,
                    order           = lecture.temporary_chapter.order,
                    product         = product
                )
                lecture_video = LectureVideo.objects.create(video_url=lecture.video_url)
                Lecture.objects.create(name=lecture.name, product=product, chapter=new_chapter, order=lecture.order, video=lecture_video)

        #lecture 내용
        for content in contents:
            image_url   = content.image.image_url
            description = content.description.description
            order       = content.order
            lecture     = Lecture.objects.get(name=content.temporary_lecture.name, product=product)

            new_description = LectureContentDescription.objects.create(description=description)
            new_image_url   = LectureContentImageUrl.objects.create(image_url=image_url)
            LectureContent.objects.create(description=new_description, image_url=new_image_url, order=order, lecture=lecture, product=product)
        
        #kit 
        for image in kit_images:
            if Kit.objects.filter(name=image.temporary_kit.name).exists():
                kit = Kit.objects.get(name=image.temporary_kit.name)
                KitSubImageUrl.objects.create(kit=kit, image_url=image.image_url)
                product.kit.add(kit)
            else:
                new_kit = Kit.objects.create(name=image.temporary_kit.name, main_image_url=image.image_url)
                KitSubImageUrl.objects.create(kit=new_kit, image_url=image.image_url)
                product.kit.add(new_kit)

        #temp 삭제
        temp.delete()

        return JsonResponse({'message':'SUCCESS'},status=200)
