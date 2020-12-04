import json

from django.views import View
from django.http  import JsonResponse

from my_settings import SECRET, ALGORITHM
from .models     import User
from core.utils  import get_hashed_pw, is_valid_name, is_valid_email, is_valid_password, checkpw, issue_token


class SignUpView(View):
    def post(self, request):
        data = json.loads(request.body)

        if 'name' not in data or 'email' not in data or 'password' not in data:
            return JsonResponse({'MESSAGE':'KEY_ERROR'}, status=400)

        name     = data['name']
        email    = data['email']
        password = data['password']

        if User.objects.filter(email = email).exists():
            return JsonResponse({'MESSAGE':'DUPLICATED_INFORMATION'}, status=400)

        if not is_valid_name(name):
            return JsonResponse({'MESSAGE':'INVALID_NAME'}, status=400)

        if not is_valid_email(email):
            return JsonResponse({'MESSAGE':'INVALID_EMAIL'}, status=400)

        if not is_valid_password(password):
            return JsonResponse({'MESSAGE':'INVALID_PASSWORD'}, status=400)

        User.objects.create(
            name     = name,
            email    = email,
            password = get_hashed_pw(password)
        )

        return JsonResponse({'MESSAGE':'SUCCESS'}, status=201)

class LogInView(View):
    def post(self, request):
        data     = json.loads(request.body)
        
        if 'email' not in data or 'password' not in data:
            return JsonResponse({'MESSAGE':'KEY_ERROR'}, status=400)

        email    = User.objects.filter(email=data['email'])
        password = data['password']

        if not email.exists():
            return JsonResponse({'MESSAGE':'NO_EXIST_USER'}, status=400)

        user = User.objects.get(email=data['email'])

        if not checkpw(password, user):
            return JsonResponse({'MESSAGE':'INVALID_PASSWORD'}, status=400)

        token = issue_token(user.id)

        return JsonResponse({'token':token, 'name':user.name}, status=200)