from datetime       import date, timedelta

from django.test    import Client, TransactionTestCase
from django.urls    import reverse
from django.db      import connection

from product.models import Product, MainCategory, SubCategory, Difficulty
from user.models    import User, Coupon
from order.models   import Order, OrderStatus, PaymentMethod
from core.utils     import issue_token

class TestSelectProductAndPaymentView(TransactionTestCase):

    def setUp(self):
        self.client = Client()
        self.PRODUCT_NOT_EXIST = 'PRODUCT_NOT_EXIST'
        self.INVALID_TOKEN     = 'INVALID_TOKEN'

        creator = User.objects.create(
            name       = '송은우',
            nick_name  = '신의 코드 송은우',
            is_creator = True
        )

        main_categories = MainCategory.objects.create(
            id   = 1,
            name = '크리에이티브'
        )

        sub_categories = SubCategory.objects.create(
            id   = 11,
            name = '데이터/개발'
        )

        difficulty = Difficulty.objects.create(
            name = '초급자'
        )

        self.product = Product.objects.create(
            name            = 'test',
            effective_time  = timedelta(days=30),
            price           = 100000.00,
            sale            = 0.0,
            start_date      = date.today(),
            thumbnail_image = 'test_thumbnail_image_url',
            main_category   = main_categories,
            sub_category    = sub_categories,
            difficulty      = difficulty,
            creator         = creator
        )

        self.coupon_1 = Coupon.objects.create(
            name          = '회원가입 축하 쿠폰',
            discount_cost = 10000.00,
            is_kit_free   = False,
            expire_date   = None,
            product       = None
        )

        self.coupon_2 = Coupon.objects.create(
            name          = '기간 한정 할인 쿠폰',
            discount_cost = 5000.00,
            is_kit_free   = False,
            expire_date   = date.today() + timedelta(days=7),
            product       = None
        )

        self.user = User.objects.create(
            id           = 5,
            name         = '김민구',
            nick_name    = '민구좌',
            password     = '1234',
            phone_number = '01011112222'
        )

        self.user.coupon.add(self.coupon_1)
        self.user.coupon.add(self.coupon_2)

        token = issue_token(self.user.id)

        self.header = {
            'HTTP_Authorization': token,
        }

    def tearDown(self):
        with connection.cursor() as cursor:
            cursor.execute('set foreign_key_checks=0')
            cursor.execute('truncate main_categories')
            cursor.execute('truncate sub_categories')
            cursor.execute('truncate difficulties')
            cursor.execute('truncate coupons')
            cursor.execute('truncate users_coupons')
            cursor.execute('truncate users')
            cursor.execute('truncate products')
            cursor.execute('set foreign_key_checks=1')

    def test_select_product_and_payment_get_fail_for_user_not_login(self):
        url = reverse('apply_product', args=[2])

        response = self.client.get(
            url,
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['MESSAGE'],
            self.INVALID_TOKEN
        )

    def test_select_product_and_payment_get_fail_for_product_not_exists(self):
        url = reverse('apply_product', args=[2])

        response = self.client.get(
            url,
            content_type='application/json',
            **self.header
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['MESSAGE'],
            self.PRODUCT_NOT_EXIST
        )

    def test_select_product_and_payment_get_success(self):
        url = reverse('apply_product', args=[1])

        response = self.client.get(
            url,
            content_type='application/json',
            **self.header
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['ORDER_INFO']['classId'],
            1
        )

    def test_select_product_and_payment_display_original_price_6_number(self):
        url = reverse('apply_product', args=[1])

        response = self.client.get(
            url,
            content_type='application/json',
            **self.header
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['ORDER_INFO']['originalPrice'],
            '100,000'
        )

    def test_select_product_and_payment_display_original_price_5_number(self):
        url = reverse('apply_product', args=[1])

        self.product.price = 10000.00
        self.product.save()

        response = self.client.get(
            url,
            content_type='application/json',
            **self.header
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['ORDER_INFO']['originalPrice'],
            '10,000'
        )

    def test_select_product_and_payment_display_original_price_4_number(self):
        url = reverse('apply_product', args=[1])

        self.product.price = 1000.00
        self.product.save()

        response = self.client.get(
            url,
            content_type='application/json',
            **self.header
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['ORDER_INFO']['originalPrice'],
            '1,000'
        )

    def test_select_product_and_payment_display_original_price_3_number(self):
        url = reverse('apply_product', args=[1])

        self.product.price = 100.00
        self.product.save()

        response = self.client.get(
            url,
            content_type='application/json',
            **self.header
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['ORDER_INFO']['originalPrice'],
            '100'
        )

    def test_select_product_and_payment_display_original_price_2_number(self):
        url = reverse('apply_product', args=[1])

        self.product.price = 10.00
        self.product.save()

        response = self.client.get(
            url,
            content_type='application/json',
            **self.header
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['ORDER_INFO']['originalPrice'],
            '10'
        )

    def test_select_product_and_payment_display_original_price_1_number(self):
        url = reverse('apply_product', args=[1])

        self.product.price = 1
        self.product.save()

        response = self.client.get(
            url,
            content_type='application/json',
            **self.header
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['ORDER_INFO']['originalPrice'],
            '1'
        )

    def test_select_product_and_payment_display_original_price_0_number(self):
        url = reverse('apply_product', args=[1])

        self.product.price = 0
        self.product.save()

        response = self.client.get(
            url,
            content_type='application/json',
            **self.header
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['ORDER_INFO']['originalPrice'],
            '0'
        )

    def test_select_product_and_payment_display_discount_price_for_sale_0per(self):
        url = reverse('apply_product', args=[1])

        response = self.client.get(
            url,
            content_type='application/json',
            **self.header
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['ORDER_INFO']['discountPrice'],
            '0'
        )

    def test_select_product_and_payment_display_discount_price_for_sale_5per(self):
        url = reverse('apply_product', args=[1])

        self.product.sale = 0.05
        self.product.save()

        response = self.client.get(
            url,
            content_type='application/json',
            **self.header
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['ORDER_INFO']['discountPrice'],
            '-5,000'
        )

    def test_select_product_and_payment_display_discount_price_for_sale_50per(self):
        url = reverse('apply_product', args=[1])

        self.product.sale = 0.5
        self.product.save()

        response = self.client.get(
            url,
            content_type='application/json',
            **self.header
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['ORDER_INFO']['discountPrice'],
            '-50,000'
        )

    def test_select_product_and_payment_display_discount_price_for_sale_100per(self):
        url = reverse('apply_product', args=[1])

        self.product.sale = 1.0
        self.product.save()

        response = self.client.get(
            url,
            content_type='application/json',
            **self.header
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['ORDER_INFO']['discountPrice'],
            '-100,000'
        )

    def test_select_product_and_payment_display_discounted_price(self):
        url = reverse('apply_product', args=[1])

        response = self.client.get(
            url,
            content_type='application/json',
            **self.header
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['ORDER_INFO']['discountedPrice'],
            '100,000'
        )

        url = reverse('apply_product', args=[1])

        self.product.sale = 0.05
        self.product.save()

        response = self.client.get(
            url,
            content_type='application/json',
            **self.header
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['ORDER_INFO']['discountedPrice'],
            '95,000'
        )

        url = reverse('apply_product', args=[1])

        self.product.sale = 0.5
        self.product.save()

        response = self.client.get(
            url,
            content_type='application/json',
            **self.header
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['ORDER_INFO']['discountedPrice'],
            '50,000'
        )

        url = reverse('apply_product', args=[1])

        self.product.sale = 1.0
        self.product.save()

        response = self.client.get(
            url,
            content_type='application/json',
            **self.header
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['ORDER_INFO']['discountedPrice'],
            '0'
        )

    def test_select_product_and_payment_user_has_coupons(self):
        url = reverse('apply_product', args=[1])

        response = self.client.get(
            url,
            content_type='application/json',
            **self.header
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(response.json()['ORDER_INFO']['couponInfo']),
            2
        )

    def test_select_product_and_payment_display_coupon_status_null(self):
        url = reverse('apply_product', args=[1])

        response = self.client.get(
            url,
            content_type='application/json',
            **self.header
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json()['ORDER_INFO']['couponInfo'][0]['couponExpiredDate'],
            '무제한'
        )

        self.assertEqual(
            response.json()['ORDER_INFO']['couponInfo'][1]['couponExpiredDate'],
            str(date.today() + timedelta(days=7))
        )

class TestOrderProductView(TransactionTestCase):

    def setUp(self):
        self.client = Client()

        main_categories = MainCategory.objects.create(
            id   = 1,
            name = '크리에이티브'
        )

        sub_categories = SubCategory.objects.create(
            id   = 11,
            name = '데이터/개발'
        )

        difficulty = Difficulty.objects.create(
            name = '초급자'
        )

        creator = User.objects.create(
            id           = 1,
            name         = '이소헌',
            nick_name    = '빛소헌',
            email        = 'leesh@email.com',
            phone_number = '01011111234',
            is_creator   = True
        )

        self.product = Product.objects.create(
            name            = '퇴근 후 함께 즐기는 코딩 모임! 직장인을 위한  취미반, 함께해요!',
            effective_time  = timedelta(days=30),
            price           = 100000.00,
            sale            = 0.0,
            start_date      = date.today(),
            thumbnail_image = 'test_product_thumbnail_image_url',
            main_category   = main_categories,
            sub_category    = sub_categories,
            difficulty      = difficulty,
            creator         = creator,
            signature       = None,
            is_deleted      = False
        )

        OrderStatus.objects.create(
            id     = 7,
            status = '수강신청'
        )

        PaymentMethod.objects.create(
            name = '무통장 입금'
        )

        self.user = User.objects.create(
            id           = 5,
            name         = '안혜수',
            nick_name    = '혜수짱',
            email        = 'anheasu@email.com',
            password     = '1234',
            phone_number = '01011111234',
            point        = 0
        )

        token = issue_token(self.user.id)

        self.header = {
            'HTTP_Authorization': token,
        }

    def tearDown(self):
        with connection.cursor() as cursor:
            cursor.execute('set foreign_key_checks=0')
            cursor.execute('truncate main_categories')
            cursor.execute('truncate sub_categories')
            cursor.execute('truncate difficulties')
            cursor.execute('truncate coupons')
            cursor.execute('truncate users')
            cursor.execute('truncate users_coupons')
            cursor.execute('truncate products')
            cursor.execute('truncate users_products')
            cursor.execute('truncate order_statuses')
            cursor.execute('truncate payment_methods')
            cursor.execute('truncate kits')
            cursor.execute('truncate products_kits')
            cursor.execute('set foreign_key_checks=1')

    def test_order_product_view_key_error_case_user_name(self):
        url = reverse('payment_product', args=[1])

        post_request_for_order = {
            'ERR_user_name'    : '01011112222',
            'phone_number'     : '01011112222',
            'post_number'      : '123-123',
            'address'          : '서울시 강남구',
            'sub_address'      : '테헤란로 427 위워크 타워(위워크 선릉 2호점)',
            'request_option'   : '하.. 문 앞에 놓고 연락 주세요..',
            'coupon_id'        : None,
            'price'            : 100000,
            'payment_method_id': 1
        }

        response = self.client.post(
            url,
            post_request_for_order,
            content_type='application/json',
            **self.header
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['MESSAGE'],
            'KEY_ERROR'
        )

    def test_order_product_view_key_error_case_phone_number(self):
        url = reverse('payment_product', args=[1])

        post_request_for_order = {
            'user_name'        : '안혜수',
            'ERR_phone_number' : '01011112222',
            'post_number'      : '123-123',
            'address'          : '서울시 강남구',
            'sub_address'      : '테헤란로 427 위워크 타워(위워크 선릉 2호점)',
            'request_option'   : '하.. 문 앞에 놓고 연락 주세요..',
            'coupon_id'        : None,
            'price'            : 100000,
            'payment_method_id': 1
        }

        response = self.client.post(
            url,
            post_request_for_order,
            content_type='application/json',
            **self.header
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['MESSAGE'],
            'KEY_ERROR'
        )

    def test_order_product_view_key_error_case_price(self):
        url = reverse('payment_product', args=[1])

        post_request_for_order = {
            'user_name'        : '안혜수',
            'phone_number'     : '01011112222',
            'post_number'      : '123-123',
            'address'          : '서울시 강남구',
            'sub_address'      : '테헤란로 427 위워크 타워(위워크 선릉 2호점)',
            'request_option'   : '하.. 문 앞에 놓고 연락 주세요..',
            'coupon_id'        : None,
            'ERR_price'        : 100000,
            'payment_method_id': 1
        }

        response = self.client.post(
            url,
            post_request_for_order,
            content_type='application/json',
            **self.header
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['MESSAGE'],
            'KEY_ERROR'
        )

    def test_order_product_view_key_error_case_payment_method_id(self):
        url = reverse('payment_product', args=[1])

        post_request_for_order = {
            'user_name'            : '안혜수',
            'phone_number'         : '01011112222',
            'post_number'          : '123-123',
            'address'              : '서울시 강남구',
            'sub_address'          : '테헤란로 427 위워크 타워(위워크 선릉 2호점)',
            'request_option'       : '하.. 문 앞에 놓고 연락 주세요..',
            'coupon_id'            : None,
            'price'                : 100000,
            'ERR_payment_method_id': 1
        }

        response = self.client.post(
            url,
            post_request_for_order,
            content_type='application/json',
            **self.header
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['MESSAGE'],
            'KEY_ERROR'
        )

    def test_request_order_fail_for_permanent_product(self):
        url = reverse('payment_product', args=[1])

        self.product.effective_time = None
        self.product.save()
        self.user.user_product.add(self.product)

        post_request_for_order = {
            'user_name'        : '안혜수',
            'phone_number'     : '01011112222',
            'post_number'      : '123-123',
            'address'          : '서울시 강남구',
            'sub_address'      : '테헤란로 427 위워크 타워(위워크 선릉 2호점)',
            'request_option'   : '하.. 문 앞에 놓고 연락 주세요..',
            'coupon_id'        : None,
            'price'            : 100000,
            'payment_method_id': 1
        }

        response = self.client.post(
            url,
            post_request_for_order,
            content_type='application/json',
            **self.header
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['MESSAGE'],
            'PERMANENT_PRODUCT'
        )

    def test_request_order_success(self):
        url = reverse('payment_product', args=[1])

        post_request_for_order = {
            'user_name'        : '안혜수',
            'phone_number'     : '01011112222',
            'post_number'      : '123-123',
            'address'          : '서울시 강남구',
            'sub_address'      : '테헤란로 427 위워크 타워(위워크 선릉 2호점)',
            'request_option'   : '하.. 문 앞에 놓고 연락 주세요..',
            'coupon_id'        : None,
            'price'            : 100000,
            'payment_method_id': 1
        }

        response = self.client.post(
            url,
            post_request_for_order,
            content_type='application/json',
            **self.header
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['MESSAGE'],
            'ORDER_SUCCESS'
        )
