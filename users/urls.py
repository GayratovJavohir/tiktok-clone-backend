from django.urls import path

from users.views import (
    RegistrationView,
    LoginView,
    UserListAPIView,
    LogoutAPIView,
    CurrentUserView,
    PostListView,
    AnotherProfileView,
    FollowView      
)
app_name = 'users'

urlpatterns = [
    path('register/', RegistrationView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('users/', UserListAPIView.as_view(), name='users-list'),
    path('profile/', CurrentUserView.as_view(), name='profile'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('profile/posts/', PostListView.as_view(), name='profile-posts'),
    path('another-profile/<int:profileId>/', AnotherProfileView.as_view(), name='another-profile'),
    path('follow/<int:profileId>/', FollowView.as_view(), name='follow'),
]
