<<<<<<< HEAD
from django.test import TestCase

# Create your tests here.
=======
import json
import bcrypt
import jwt

from django.test import TestCase, Client
from django.http import JsonResponse

from .models     import User
from core.utils  import get_hashed_pw, checkpw, issue_token

class UserSignUpTest(TestCase):
    def setUp(self):
        self.URL           = '/user/signup'
        self.client        = Client()
        self.PASS_NAME     = 'jaehoon'
        self.PASS_EMAIL    = 'jae@gmail.com'
        self.PASS_PASSWORD = '12345678'

        self.TEST_NAME     = 'test'
        self.TEST_EMAIL    = 'test@gmail.com'
        self.TEST_PASSWORD = '123456789'

        self.user = User(
            name     = self.TEST_NAME,
            email    = self.TEST_EMAIL,
            password = self.TEST_PASSWORD,
            )
        self.user.save()

    def tearDown(self):
        User.objects.all().delete()

    def test_post_sign_up_success(self):
        request = {
            'name'     : self.PASS_NAME,
            'email'    : self.PASS_EMAIL,
            'password' : self.PASS_PASSWORD
        }

        response = self.client.post(self.URL, request, content_type = 'application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['MESSAGE'], 'SUCCESS')

    def test_post_sign_up_key_error(self):
        requests = [
            {'name'     : self.PASS_NAME},
            {'email'    : self.PASS_EMAIL},
            {'password' : self.PASS_PASSWORD},
            {
                'name'      : self.PASS_NAME,
                'password'  : self.PASS_PASSWORD
                },
            {
                'name'      : self.PASS_NAME,
                'email'     : self.PASS_EMAIL
                },
            {
                'email'     : self.PASS_EMAIL,
                'password'  : self.PASS_PASSWORD
                }]

            response = self.client.post(self.URL, request, content_type='application/json')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()['MESSAGE'], 'KEY_ERROR')

    def test_post_sign_up_duplicate_info(self):
        request = {
            'name'     : self.TEST_NAME,
            'email'    : self.TEST_EMAIL,
            'password' : self.TEST_PASSWORD
        }

        response = self.client.post(self.URL, request, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['MESSAGE'], 'DUPLICATE_INFORMATION')

    def test_post_sign_up_is_valid_name(self):
        request = {
            'name'     : '123456789012345678901234',
            'email'    : self.PASS_EMAIL,
            'password' : self.PASS_PASSWORD
        }

        response = self.client.post(self.URL, request, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['MESSAGE'],'INVALID_NAME')

    def test_post_sign_up_is_valid_email(self):
        request = [
            {
            'name'     : self.PASS_NAME,
            'email'    : 'test.com',
            'password' : self.PASS_PASSWORD
            },
            {
            'name'     : self.PASS_NAME,
            'email'    : 'test@com',
            'password' : self.PASS_PASSWORD
            }]

            response = self.client.post(self.URL, request, content_type='application/json')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()['MESSAGE'], 'INVALID_EMAIL')

    def test_post_sign_up_is_valid_password(self):
        request =  [
            {
            'name'     : self.PASS_NAME,
            'email'    : self.PASS_EMAIL,
            'password' : '12345'
            },
            {
            'name'     : self.PASS_NAME,
            'email'    : self.PASS_EMAIL,
            'password' : '123456789012345678901234567'
            }]

            response = self.client.post(self.URL, request, content_type='application/json')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()['MESSAGE'], 'INVALID_PASSWORD')

class UserLogInTest(TestCase):
    def setUp(self):
        self.URL = '/user/login'
        self.SIGN_UP_URL = '/user/signup'
        self.client = Client()
        self.PASS_NAME         = 'jaehoon'
        self.PASS_EMAIL        = 'jae@gmail.com'
        self.PASS_PASSWORD     = '12345678'

        self.TEST_NAME         = 'test'
        self.TEST_EMAIL        = 'test@gmail.com'
        self.TEST_PASSWORD     = '123456789'

        request = {
            'name'     : self.TEST_NAME,
            'email'    : self.TEST_EMAIL,
            'password' : self.TEST_PASSWORD,
        }
        self.client.post(self.SIGN_UP_URL, request, content_type='application/json')
        self.user = User.objects.get(email=self.TEST_EMAIL)
        self.access_token = issue_token(self.user.pk)

    def tearsDown(self):
        pass

    def test_post_log_in_key_error(self):
        request = [
            {'email'    : self.PASS_EMAIL},
            {'password' : self.PASS_PASSWORD}
        ]

        response = self.client.post(self.URL, request, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['MESSAGE'], 'KEY_ERROR')
    
    def test_post_log_in_is_user_exist(self):
        request = {
            'email'    : self.PASS_EMAIL,
            'password' : self.TEST_PASSWORD
        }
        response = self.client.post(self.URL, request, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['MESSAGE'], 'NO_EXIST_USER')


    def test_post_log_in_success(self):
        request = {
            'email'    : self.TEST_EMAIL,
            'password' : self.TEST_PASSWORD
        }
        
        response = self.client.post(self.URL, request, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['name'], self.user.name)
        self.assertEqual(response.json()['token'], self.access_token)
        
    def test_post_log_in_check_pw(self):
        request = {
            'email'    : self.TEST_EMAIL,
            'password' : self.PASS_PASSWORD
        }
        response = self.client.post(self.URL, request, content_type='application/json')
        hashed_pw = get_hashed_pw(self.PASS_PASSWORD)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['MESSAGE'], 'INVALID_PASSWORD')
        self.assertEqual(checkpw(hashed_pw, self.user), False)
>>>>>>> 3a472ce... Add: SignUpView
