from django.urls import path
from .views      import SignUpView, LogInView, KakaoLogInView

urlpatterns = [
    path('/signup', SignUpView.as_view()),
    path('/login', LogInView.as_view()),
    path('/login/kakao', KakaoLogInView.as_view()),
]

