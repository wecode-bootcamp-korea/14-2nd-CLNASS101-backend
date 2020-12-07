import json
import requests

from django.views import View
from django.http import JsonResponse

from my_settings import SECRET, ALGORITHM
from .models import User
from core.utils import (
    get_hashed_pw,
    is_valid_name,
    is_valid_email,
    is_valid_password,
    checkpw,
    issue_token,
)


class SignUpView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)

            name = data["name"]
            email = data["email"]
            password = data["password"]

            if User.objects.filter(email=email).exists():
                return JsonResponse({"MESSAGE": "DUPLICATE_INFORMATION"}, status=409)

            if not is_valid_name(name):
                return JsonResponse({"MESSAGE": "INVALID_NAME"}, status=400)

            if not is_valid_email(email):
                return JsonResponse({"MESSAGE": "INVALID_EMAIL"}, status=400)

            if not is_valid_password(password):
                return JsonResponse({"MESSAGE": "INVALID_PASSWORD"}, status=400)

            User.objects.create(
                name=name,
                email=email,
                password=get_hashed_pw(password)
            )

            return JsonResponse({"MESSAGE": "SUCCESS"}, status=201)
        except json.JSONDecodeError as e:
            return JsonResponse({"MESSAGE": f"JSON_ERROR:{e}"}, status=400)
        except TypeError:
            return JsonResponse({"MESSAGE": "TYPE_ERROR"}, status=400)
        except KeyError as e:
            return JsonResponse({"MESSAGE": f"KEY_ERROR:{e}"}, status=400)


class LogInView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            user = User.objects.get(email=data["email"])
            password = data["password"]

            if not checkpw(password, user):
                return JsonResponse({"MESSAGE": "INVALID_PASSWORD"}, status=401)

            token = issue_token(user.id)

            return JsonResponse({"token": token, "name": user.name}, status=200)

        except User.DoesNotExist:
            return JsonResponse({"MESSAGE": "NO_EXIST_USER"}, status=401)
        except json.JSONDecodeError as e:
            return JsonResponse({"MESSAGE": f"JSON_ERROR:{e}"}, status=400)
        except TypeError:
            return JsonResponse({"MESSAGE": "TYPE_ERROR"}, status=400)
        except KeyError as e:
            return JsonResponse({"MESSAGE": f"KEY_ERROR:{e}"}, status=400)


class KakaoLogInView(View):
    def post(self, request):
        try:
            access_token = request.headers["Authorization"]

            if not access_token:
                return JsonResponse({'MESSAGE': 'TOKEN_REQUIRED'}, status=400)

            url = "https://kapi.kakao.com/v2/user/me"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-type": "application/x-www-form-urlencoded; charset=utf-8",
            }
            response = requests.get(url, headers=headers)
            kakao_user = json.loads(response)

            if not 'email' in kakao_user['kakao_account']:
                return JsonResponse({'MESSAGE': 'EMAIL_REQUIRED'}, status=405)

            kakao_user = User.objects.get_or_create(
                kakao_id=kakao_user["id"],
                name=kakao_user["properties"]["nickname"],
                email=kakao_user["kakao_account"]["email"],
                profile_image=kakao_user["properties"]["profile_image"],
            )[0]

            token = issue_token(kakao_user.id)

            return JsonResponse({"token": token, "name": kakao_user.name, "id": kakao_user.id}, status=200)
        except json.JSONDecodeError as e:
            return JsonResponse({"MESSAGE": f"JSON_ERROR:{e}"}, status=400)
        except User.DoesNotExist:
            return JsonResponse({"MESSAGE": "NO_EXIST_USER"}, status=401)
        except TypeError:
            return JsonResponse({"MESSAGE": "TYPE_ERROR"}, status=400)
        except KeyError as e:
            return JsonResponse({"MESSAGE": f"KEY_ERROR:{e}"}, status=400)
