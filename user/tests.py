import json

from django.test import TestCase, Client
from django.http import JsonResponse

from core.utils  import get_hashed_pw, checkpw, issue_token
from .models     import User

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
        requests = []
        requests.append({'email'    : self.PASS_EMAIL})
        requests.append({'password' : self.PASS_PASSWORD})

        for request in requests:
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

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['MESSAGE'], 'INVALID_PASSWORD')
        self.assertEqual(checkpw(hashed_pw, self.user), False)