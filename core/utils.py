import jwt
import bcrypt
import re

from django.http import JsonResponse

from my_settings import SECRET, ALGORITHM
from user.models import User

def login_decorator(login_required):
    def real_decorator(func):
        def wrapper(self, request, *args, **kwargs):
            try:
                token = request.headers.get('Authorization', None)
                
                if not token and not login_required:
                    request.user = User.objects.filter(id=0)
                    return func(self, request, *args, **kwargs)
                
                payload = jwt.decode(
                    token,
                    SECRET['secret'],
                    algorithm=ALGORITHM['algorithm']
                )
                user = User.objects.get(id=payload['user_id'])
                request.user = user

            except jwt.exceptions.DecodeError:
                return JsonResponse({"MESSAGE": "INVALID_TOKEN"}, status=400)

            except User.DoesNotExist:
                return JsonResponse({"MESSAGE": "INVALID_USER"}, status=401)

            return func(self, request, *args, **kwargs)

        return wrapper

    return real_decorator


def get_hashed_pw(password):
    return bcrypt.hashpw(password.encode("UTF-8"), bcrypt.gensalt()).decode("UTF-8")


def is_valid_name(name):
    return re.match('^[a-z가-힣A-Z0-9]{1,20}$', name)


def is_valid_email(email):
    return re.match('^[a-zA-Z0-9_+.-]+@([a-zA-Z0-9-]+\.)+[a-zA-Z0-9]+$', email)


def is_valid_password(password):
    return re.match('^[a-z가-힣A-Z0-9]{8,25}$', password)


def checkpw(password, user_object):
    return bcrypt.checkpw(password.encode('UTF-8'), user_object.password.encode('UTF-8'))


def issue_token(user_id):
    return jwt.encode({'user_id': user_id}, SECRET['secret'], algorithm=ALGORITHM['algorithm']).decode('UTF-8')
