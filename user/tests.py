import json
import bcrypt
import jwt

from datetime import date, timedelta

from django.test import TestCase, Client
from unittest.mock import MagicMock, patch

from .models import User, ProductLike
from kit.models import Kit
from core.utils import (
    get_hashed_pw,
    checkpw,
    issue_token)
from product.models import (
    Product,
    SubCategory,
    MainCategory,
    Difficulty)

class UserSignUpTest(TestCase):
    def setUp(self):
        self.URL = '/user/signup'
        self.client = Client()
        self.PASS_NAME = 'jaehoon'
        self.PASS_EMAIL = 'jae@gmail.com'
        self.PASS_PASSWORD = '12345678'

        self.TEST_NAME = 'test'
        self.TEST_EMAIL = 'test@gmail.com'
        self.TEST_PASSWORD = '123456789'

        self.user = User(
            name=self.TEST_NAME,
            email=self.TEST_EMAIL,
            password=self.TEST_PASSWORD,
        )
        self.user.save()

    def tearDown(self):
        User.objects.all().delete()

    def test_post_sign_up_success(self):
        request = {
            'name': self.PASS_NAME,
            'email': self.PASS_EMAIL,
            'password': self.PASS_PASSWORD
        }

        response = self.client.post(
            self.URL, request, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['MESSAGE'], 'SUCCESS')

    def test_post_sign_up_key_error(self):
        requests = [
            {'name': self.PASS_NAME},
            {'email': self.PASS_EMAIL},
            {'password': self.PASS_PASSWORD},
            {
                'name': self.PASS_NAME,
                'password': self.PASS_PASSWORD
            },
            {
                'name': self.PASS_NAME,
                'email': self.PASS_EMAIL
            },
            {
                'email': self.PASS_EMAIL,
                'password': self.PASS_PASSWORD
            }]

        response = self.client.post(
            self.URL, request, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['MESSAGE'], 'KEY_ERROR')

    def test_post_sign_up_duplicate_info(self):
        request = {
            'name': self.TEST_NAME,
            'email': self.TEST_EMAIL,
            'password': self.TEST_PASSWORD
        }

        response = self.client.post(
            self.URL, request, content_type='application/json')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['MESSAGE'], 'DUPLICATE_INFORMATION')

    def test_post_sign_up_is_valid_name(self):
        request = {
            'name': '123456789012345678901234',
            'email': self.PASS_EMAIL,
            'password': self.PASS_PASSWORD
        }

        response = self.client.post(
            self.URL, request, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['MESSAGE'], 'INVALID_NAME')

    def test_post_sign_up_is_valid_email(self):
        request = [
            {
                'name': self.PASS_NAME,
                'email': 'test.com',
                'password': self.PASS_PASSWORD
            },
            {
                'name': self.PASS_NAME,
                'email': 'test@com',
                'password': self.PASS_PASSWORD
            }]

        response = self.client.post(
            self.URL, request, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['MESSAGE'], 'INVALID_EMAIL')

    def test_post_sign_up_is_valid_password(self):
        request = [
            {
                'name': self.PASS_NAME,
                'email': self.PASS_EMAIL,
                'password': '12345'
            },
            {
                'name': self.PASS_NAME,
                'email': self.PASS_EMAIL,
                'password': '123456789012345678901234567'
            }]

        response = self.client.post(
            self.URL, request, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['MESSAGE'], 'INVALID_PASSWORD')


class UserLogInTest(TestCase):
    def setUp(self):
        self.URL = '/user/login'
        self.SIGN_UP_URL = '/user/signup'
        self.client = Client()
        self.PASS_NAME = 'jaehoon'
        self.PASS_EMAIL = 'jae@gmail.com'
        self.PASS_PASSWORD = '12345678'

        self.TEST_NAME = 'test'
        self.TEST_EMAIL = 'test@gmail.com'
        self.TEST_PASSWORD = '123456789'

        request = {
            'name': self.TEST_NAME,
            'email': self.TEST_EMAIL,
            'password': self.TEST_PASSWORD,
        }
        self.client.post(self.SIGN_UP_URL, request,
                         content_type='application/json')
        self.user = User.objects.get(email=self.TEST_EMAIL)
        self.access_token = issue_token(self.user.pk)

    def tearsDown(self):
        pass

    def test_post_log_in_key_error(self):
        request = [
            {'email': self.PASS_EMAIL},
            {'password': self.PASS_PASSWORD}
        ]

        response = self.client.post(
            self.URL, request, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['MESSAGE'], 'KEY_ERROR')

    def test_post_log_in_is_user_exist(self):
        request = {
            'email': self.PASS_EMAIL,
            'password': self.TEST_PASSWORD
        }
        response = self.client.post(
            self.URL, request, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['MESSAGE'], 'NO_EXIST_USER')

    def test_post_log_in_success(self):
        request = {
            'email': self.TEST_EMAIL,
            'password': self.TEST_PASSWORD
        }

        response = self.client.post(
            self.URL, request, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['name'], self.user.name)
        self.assertEqual(response.json()['token'], self.access_token)

    def test_post_log_in_check_pw(self):
        request = {
            'email': self.TEST_EMAIL,
            'password': self.PASS_PASSWORD
        }
        response = self.client.post(
            self.URL, request, content_type='application/json')
        hashed_pw = get_hashed_pw(self.PASS_PASSWORD)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['MESSAGE'], 'INVALID_PASSWORD')
        self.assertEqual(checkpw(hashed_pw, self.user), False)

    def test_post_kakao_login_wrong_token(self):
        header = {'HTTP_Authorization': 'wrong_token'}
        response = self.client.post(
            '/user/login/kakao', content_type='application/json', **header)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'MESSAGE': 'INVALID_TOKEN'})

    def test_post_kakao_login_key_error(self):
        header = {'HTTP_Wrong': 'wrong_token'}
        response = self.client.post(
            '/user/login/kakao', content_type='application/json', **header)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'MESSAGE': 'KEY_ERROR'})

    @patch('user.views.requests')
    def test_post_kakao_login_success(self, mocked_request):
        class FakeResponse:
            def json(self):
                return {
                    'id': 1548993291,
                    'properties': {
                        'nickname': 'test_nickname',
                        'profile_image': 'test_image_url',
                    },
                    'kakao_account': {
                        'email': 'test@email.com',
                    }
                }
        mocked_request.get = MagicMock(return_value=FakeResponse())
        header = {'HTTP_Authorization': 'fake_token'}
        response = self.client.post(
            '/user/login/kakao', content_type='application/json', **header)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'token')


class ProductSearchTest(TestCase):
    def setUp(self):
        self.main_categories = MainCategory.objects.create(
            id=1,
            name='크리에이티브'
        )

        self.sub_categories = SubCategory.objects.create(
            id=1,
            name='개발'
        )
        self.difficulty = Difficulty.objects.create(
            name='초급자'
        )
        self.kit = Kit.objects.create(
            name='test_kit',
            main_image_url='image_url',
            price=10000,
            description='test_description'
        )
        self.creator = User.objects.create(
            name='이소헌',
            nick_name='신의 코드 밫소헌',
            is_creator=True
        )

        self.user = User.objects.create(
            name='재훈',
            email='jae@gmail.com',
            password='12345678',
            is_creator=False
        )
        Product.objects.create(
            name='퇴근 후 함께 즐기는 코딩 모임! 직장인을 위한  취미반, 함께해요!',
            thumbnail_image='test_thumbnail_image_url',
            effective_time=timedelta(days=30),
            price=10000.00,
            sale=0.05,
            start_date=date.today(),
            main_category=self.main_categories,
            sub_category=self.sub_categories,
            difficulty=self.difficulty,
            creator=self.creator
        )

    def tearDown(self):
        Product.objects.all().delete()
        SubCategory.objects.all().delete()

    def test_get_search_success(self):
        client = Client()
        self.maxDiff = None
        response = client.get('/user/search?search=코딩')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(),
                         {
            'id': 3,
            'title': '퇴근 후 함께 즐기는 코딩 모임! 직장인을 위한  취미반, 함께해요!',
            'thumbnail': 'test_thumbnail_image_url',
            'subCategory': self.sub_categories.name,
            'creator': '이소헌',
            'isLiked': False,
            'likeCount': 0,
            'price': 10000,
            'sale': 0.05,
            'finalPrice': 9500
        }
        )

    def test_get_search_fail(self):
        client = Client()

        response = client.get('/user/search?sch=클래스',
                              content_type='application/json')

        print(response)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(),
                         {
            'MESSAGE': 'WRONG_KEY'
        }
        )

    def test_get_search_no_result(self):
        client = Client()
        response = client.get('/user/search?search=핡')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(),
                         {
            'MESSAGE': 'NO_RESULT'
        }
        )
                    'id': 1548993291, 
                    'properties': {
                        'nickname': 'test_nickname',
                        'profile_image': 'test_image_url',
                        },
                    'kakao_account': {
                        'email': 'test@email.com',
                        }
                    }
        mocked_request.get = MagicMock(return_value = FakeResponse())
        header = {'HTTP_Authorization':'fake_token'}
        response = self.client.post('/user/login/kakao', content_type='application/json', **header)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'token')
