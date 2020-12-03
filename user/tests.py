import json
import bcrypt
import jwt

from django.test import TestCase, Client
from django.http import JsonResponse

from .models     import User

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
        requests = []
        requests.append({
            'name'     : self.PASS_NAME
        })
        requests.append({
            'email'    : self.PASS_EMAIL
        })
        requests.append({
            'password' : self.PASS_PASSWORD
        })
        requests.append({
            'name'     : self.PASS_NAME,
            'password' : self.PASS_PASSWORD
        })
        requests.append({
            'name'     : self.PASS_NAME,
            'password' : self.PASS_PASSWORD
        })
        requests.append({
            'name'  : self.PASS_NAME,
            'email' : self.PASS_EMAIL
        })
        requests.append({
            'email'    : self.PASS_EMAIL,
            'password' : self.PASS_PASSWORD
        })

        for request in requests:
            response = self.client.post(self.URL, request, content_type='application/json')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()['MESSAGE'], 'KEY_ERROR')

    def test_post_sign_up_duplicated_info(self):
        request = {
            'name'     : self.TEST_NAME,
            'email'    : self.TEST_EMAIL,
            'password' : self.TEST_PASSWORD
        }

        response = self.client.post(self.URL, request, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['MESSAGE'], 'DUPLICATED_INFORMATION')

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
        requests = []
        requests.append({
            'name'     : self.PASS_NAME,
            'email'    : 'test.com',
            'password' : self.PASS_PASSWORD
        })
        requests.append({
            'name'     : self.PASS_NAME,
            'email'    : 'test@com',
            'password' : self.PASS_PASSWORD
        })

        for request in requests:
            response = self.client.post(self.URL, request, content_type='application/json')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()['MESSAGE'], 'INVALID_EMAIL')

    def test_post_sign_up_is_valid_password(self):
        requests =  []
        requests.append({
            'name'     : self.PASS_NAME,
            'email'    : self.PASS_EMAIL,
            'password' : '12345'
        })
        requests.append({
            'name'     : self.PASS_NAME,
            'email'    : self.PASS_EMAIL,
            'password' : '123456789012345678901234567'
        })

        for request in requests:
            response = self.client.post(self.URL, request, content_type='application/json')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()['MESSAGE'], 'INVALID_PASSWORD')
