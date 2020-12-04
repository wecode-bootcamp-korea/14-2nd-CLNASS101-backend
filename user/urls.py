from django.urls import path
from .views      import SignUpView, LogInView

urlpatterns = [
    path('/login',  LogInView.as_view()),
    path('/signup', SignUpView.as_view()),
]

