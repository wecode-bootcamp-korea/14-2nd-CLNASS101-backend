import json

from django.views import View
from django.http  import JsonResponse

from my_settings import SECRET, ALGORITHM
from .models     import User
from core.utils  import get_hashed_pw, is_valid_name, is_valid_email, is_valid_password, checkpw, issue_token

class LogInView(View):
    def post(self, request):
        if 'email' not in data or 'password' not in data:
            return JsonResponse({'MESSAGE':'KEY_ERROR'}, status=400)

        data     = json.loads(request.body)
        email    = User.objects.filter(email=data['email'])
        password = data['password']

        if not email.exists():
            return JsonResponse({'MESSAGE':'NO_EXIST_USER'}, status=400)

        user = User.objects.get(email=data['email'])

        if not checkpw(password, user):
            return JsonResponse({'MESSAGE':'INVALID_PASSWORD'}, status=400)

        token = issue_token(user.id)

        return JsonResponse({'token':token, 'name':user.name}, status=200)