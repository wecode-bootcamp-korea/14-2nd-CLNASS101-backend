from django.urls import path
from .views import SignUpView, LogInView, KakaoLogInView, SearchView

urlpatterns = [
    path('/signup', SignUpView.as_view()),
    path('/login', LogInView.as_view()),
    path('/login/kakao', KakaoLogInView.as_view()),
    path('/search', SearchView.as_view()),
]
