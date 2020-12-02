from datetime       import date, timedelta

from django.test    import Client, TransactionTestCase
from django.urls    import reverse
from django.db      import connection

from product.models import (
    Product,
    ProductSubImage,
    MainCategory,
    SubCategory,
    Difficulty,
    Chapter,
    Community,
    Signature
)
from user.models    import User
from kit.models     import Kit
from core.utils     import issue_token

class TestProductDetailView(TransactionTestCase):
    
    @classmethod
    def setUpTestData(cls):
        pass
    
    def setUp(self):
        self.client = Client()
        
        self.PRODUCT_NOT_EXIST = 'PRODUCT_NOT_EXIST'
        
        self.main_categories = MainCategory.objects.create(
            id   = 1,
            name = '크리에이티브'
        )
        
        self.sub_categories = SubCategory.objects.create(
            id   = 11,
            name = '데이터/개발'
        )
        
        self.difficulty = Difficulty.objects.create(
            name = '초급자'
        )
        
        self.kit = Kit.objects.create(
            name           = 'test_kit',
            main_image_url = 'image_url',
            price          = 10000,
            description    = 'test_description'
        )
        
        self.creator = User.objects.create(
            name       = '송은우',
            nick_name  = '신의 코드 송은우',
            is_creator = True
        )
        
        self.user = User.objects.create(
            name       = '김민구',
            nick_name  = '민구좌',
            password   = '1234',
            is_creator = False
        )

        token = issue_token(self.user.id)
        
        self.header = {
            'HTTP_Authorization': token,
        }
        
        self.signature = Signature.objects.create(
            name = '기용좌'
        )
        
        self.product = Product.objects.create(
            name            = '퇴근 후 함께 즐기는 코딩 모임! 직장인을 위한  취미반, 함께해요!',
            effective_time  = timedelta(days=30),
            price           = 10000.00,
            sale            = 0.05,
            start_date      = date.today(),
            thumbnail_image = 'test_thumbnail_image_url',
            main_category   = self.main_categories,
            sub_category    = self.sub_categories,
            difficulty      = self.difficulty,
            creator         = self.creator
        )
        
        self.product.kit.add(self.kit)
        
        for i in range(3):
            ProductSubImage.objects.create(
                image_url  = 'test_url' + str(i),
                product_id = self.product.id
            )
        
        for i in range(3, 0, -1):
            Chapter.objects.create(
                name            = 'chapter' + str(i),
                product_id      = self.product.id,
                order           = i,
                thumbnail_image = 'image_url'
            )
        
        for i in range(10, 0, -1):
            Community.objects.create(
                description='test_community_description' + str(i),
                user_id=self.user.id,
                product_id=self.product.id,
            )
        
        for i in range(3):
            Community.objects.create(
                description = 'test_creator_community_description' + str(i),
                user_id     = self.creator.id,
                product_id  = self.product.id,
            )
    
    def tearDown(self):
        with connection.cursor() as cursor:
            cursor.execute('set foreign_key_checks=0')
            cursor.execute('truncate main_categories')
            cursor.execute('truncate sub_categories')
            cursor.execute('truncate users')
            cursor.execute('truncate products')
            cursor.execute('truncate chapters')
            cursor.execute('truncate communities')
            cursor.execute('truncate users_coupons')
            cursor.execute('truncate coupons')
            cursor.execute('truncate difficulties')
            cursor.execute('truncate kits')
            cursor.execute('truncate recently_views')
            cursor.execute('set foreign_key_checks=1')
    
    def test_product_detail_get_fail_wrong_product_id(self):
        url = reverse('products', args=[2])
        
        response = self.client.get(
            url, content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['MESSAGE'],
            self.PRODUCT_NOT_EXIST
        )
        
    def test_product_detail_get_fail_product_deleted(self):
        url = reverse('products', args=[1])
        
        self.product.is_deleted = True
        self.product.save()
        
        response = self.client.get(
            url, content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['MESSAGE'],
            self.PRODUCT_NOT_EXIST
        )
    
    def test_product_detail_get_success_with_no_token(self):
        url = reverse('products', args=[1])
        
        response = self.client.get(url, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['CLASS']['classId'],
            1
        )
        
    def test_product_detail_get_success_with_token(self):
        url = reverse('products', args=[1])
        
        response = self.client.get(
            url,
            content_type='application/json',
            **self.header
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['CLASS']['classId'],
            1
        )

    def test_product_detail_get_success_with_token_display_is_like(self):
        url = reverse('products', args=[1])
        
        self.user.product_like.add(self.product)
        
        response = self.client.get(
            url,
            content_type='application/json',
            **self.header
        )
        
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(
            response.json()['CLASS']['isLike'],
            True
        )
        self.assertEqual(
            response.json()['CLASS']['likeCount'],
            1
        )
    
    def test_product_detail_product_sub_image_exists(self):
        url = reverse('products', args=[1])
    
        response = self.client.get(url, content_type='application/json')
    
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(
            response.json()['CLASS']['subImages'],
            []
        )
    
    def test_product_detail_chapters_order_is_valid(self):
        url = reverse('products', args=[1])
        
        response = self.client.get(url, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [
                curriculums['order']
                for curriculums in response.json()['CLASS']['curriculum']
            ],
            [1, 2, 3]
        )
    
    def test_product_detail_kits_exists(self):
        url = reverse('products', args=[1])
        
        response = self.client.get(url, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(
            response.json()['CLASS']['kitInfo'],
            []
        )
    
    def test_product_detail_community_order_by_updated_at(self):
        url = reverse('products', args=[1])
        
        response = self.client.get(url, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(
            response.json()['CLASS']['community'][0]['communityId'],
            len(response.json()['CLASS']['community'])
        )
    
    def test_display_is_take_class_take_possible_now(self):
        url = reverse('products', args=[1])
        
        response = self.client.get(url, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['CLASS']['isTakeClass'],
            '바로 수강 가능'
        )
    
    def test_display_is_take_class_take_impossible_now(self):
        url = reverse('products', args=[1])
        
        self.product.start_date = '2020-12-31'
        self.product.save()
        
        response = self.client.get(url, content_type='application/json')
        
        print(response.json()['CLASS']['isTakeClass'])
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['CLASS']['isTakeClass'],
            '12월 31일 부터 수강 가능'
        )
    
    def test_display_class_owner_is_user(self):
        url = reverse('products', args=[1])
        
        response = self.client.get(url, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['CLASS']['classOwner'],
            '신의 코드 송은우'
        )
    
    def test_display_class_owner_is_signature(self):
        url = reverse('products', args=[1])
        
        self.product.creator = None
        self.product.signature = self.signature
        self.product.save()
        
        response = self.client.get(url, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            '기용좌',
            response.json()['CLASS']['classOwner']
        )
