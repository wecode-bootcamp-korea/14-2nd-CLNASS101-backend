from django.urls import path

from product.views import ProductDetailView, LectureDetailView, ClassDetailView, MainPageView
from user.views import CommunityView, CommunityCommentView, LectureCommentView, CommunityLikeView, \
    ProductLikeView

urlpatterns = [
    path('/main', MainPageView.as_view()),
    path('/<int:product_id>', ProductDetailView.as_view(), name='products'),
    path('/<int:product_id>/challenge', ClassDetailView.as_view(), name='class_detail'),
    path('/chapters/<int:chapter_id>/lecture/<int:lecture_id>',
         LectureDetailView.as_view(), name='lectures'),
    path('/community', CommunityView.as_view()),
    path('/community/<int:id>', CommunityView.as_view()),
    path('/community/comment', CommunityCommentView.as_view()),
    path('/community/comment/<int:id>', CommunityCommentView.as_view()),
    path('/community/like', CommunityLikeView.as_view()),
    path('/lecture/comment', LectureCommentView.as_view()),
    path('/lecture/comment/<int:id>', LectureCommentView.as_view()),
    path('/like', ProductLikeView.as_view()),
]