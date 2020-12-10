from django.urls import path

from product.views import ProductDetailView, CommunityView, CommunityCommentView, LectureCommentView, CommunityLikeView, ProductLikeView

urlpatterns = [
    path('/<int:product_id>', ProductDetailView.as_view(), name='products'),
    path('/community', CommunityView.as_view()),
    path('/community/<int:id>', CommunityView.as_view()),
    path('/community/comment', CommunityCommentView.as_view()),
    path('/community/comment/<int:id>', CommunityCommentView.as_view()),
    path('/community/like', CommunityLikeView.as_view()),
    path('/lecture/comment', LectureCommentView.as_view()),
    path('/lecture/comment/<int:id>', LectureCommentView.as_view()),
    path('/like', ProductLikeView.as_view()),
]