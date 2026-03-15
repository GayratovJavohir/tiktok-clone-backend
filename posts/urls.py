from django.urls import path
from rest_framework.routers import DefaultRouter

from posts import views
from posts.views import PostViewSet, FollowingViewSet, StoryViewSet

app_name = 'posts'

router = DefaultRouter()
router.register('posts', PostViewSet, basename='posts')
router.register('musics', views.MusicViewSet, basename='musics')
router.register('comments', views.CommentViewSet, basename='comments')
router.register('reply_comments', views.ReplyCommentViewSet, basename='reply_comments')
router.register('following', FollowingViewSet, basename='following')
router.register('friends', views.FriendViewSet, basename='friends')
router.register('stories', StoryViewSet, basename='stories')

urlpatterns = [
    path('hashtags/', views.HashtagListCreateAPIView.as_view(), name='hashtag-list-create'),
    path('hashtags/<int:pk>/', views.HashtagUpdateAPIView.as_view(), name='hashtag-update'),
    path('hashtags/delete/<int:pk>/', views.HashtagDeleteAPIView.as_view(), name='hashtag-delete'),
    path('hashtag/<int:pk>/', views.HashtagRetrieveAPIView.as_view(), name='hashtag-retrieve'),
]

urlpatterns += router.urls