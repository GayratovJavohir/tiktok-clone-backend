from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView, ListCreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework import filters
from rest_framework.parsers import MultiPartParser, FormParser

from users.models import UserModel, Follow
from users.serializers import RegistrationSerializer, LoginSerializer, UserModelSerializer, ProfileSerializer
from posts.models import Post
from posts.serializers import PostSerializer


class RegistrationView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response({'Message': "user is created"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data
            refresh = RefreshToken.for_user(user)

            return Response({
                "refresh": str(refresh),
                "access_token": str(refresh.access_token)
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListAPIView(ListAPIView):
    queryset = UserModel.objects.all()
    serializer_class = UserModelSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'first_name']
    permission_classes = [AllowAny]


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {'error': 'Invalid refresh token'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {'message': 'Logged out successfully'},
            status=status.HTTP_200_OK
        )


class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = ProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=200)


class AnotherProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        profile_id = kwargs.get('profileId')

        user = UserModel.objects.get(pk=profile_id)
        serializer = ProfileSerializer(user, context={"request": request})

        return Response(serializer.data)


class PostListView(ListCreateAPIView):
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer


class FollowView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        profile_id = kwargs.get('profileId')

        try:
            profile = UserModel.objects.get(pk=profile_id)
        except UserModel.DoesNotExist:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if user == profile:
            return Response(
                {'error': 'You cannot follow yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )

        follow, created = Follow.objects.get_or_create(
            following_user=user,
            followed_user=profile
        )

        if not created:
            return Response(
                {"followed": True},
                status=status.HTTP_200_OK
            )

        return Response(
            {"followed": True},
            status=status.HTTP_200_OK
        )

    def delete(self, request, *args, **kwargs):
        user = request.user
        profile_id = kwargs.get('profileId')

        try:
            profile = UserModel.objects.get(pk=profile_id)
        except UserModel.DoesNotExist:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        follow = Follow.objects.filter(
            following_user=user,
            followed_user=profile
        ).first()

        if not follow:
            return Response(
                {"followed": False},
                status=status.HTTP_200_OK
            )

        follow.delete()
        return Response(
            {"followed": False},
            status=status.HTTP_200_OK
        )

