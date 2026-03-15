from rest_framework import permissions, viewsets
from rest_framework.generics import UpdateAPIView, DestroyAPIView, RetrieveAPIView, ListCreateAPIView

from posts.models import Hashtag, Music, Post, Like, Comment, CommentLike, ReplyComment, ReplyCommentLike, Story
from posts.permissions import IsOwnerOrAdmin
from posts.serializers import HashtagModelSerializer, MusicSerializer, PostSerializer, CommentSerializer, ReplyCommentSerializer, FollowingSerializer, FriendSerializer, StorySerializer
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from users.models import UserModel
from django.utils import timezone
from datetime import timedelta



class HashtagListCreateAPIView(ListCreateAPIView):
    queryset = Hashtag.objects.all()
    serializer_class = HashtagModelSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]


class HashtagRetrieveAPIView(RetrieveAPIView):
    queryset = Hashtag.objects.all()
    serializer_class = HashtagModelSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'pk'


class HashtagUpdateAPIView(UpdateAPIView):
    queryset = Hashtag.objects.all()
    serializer_class = HashtagModelSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'pk'


class HashtagDeleteAPIView(DestroyAPIView):
    queryset = Hashtag.objects.all()
    serializer_class = HashtagModelSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'pk'


class MusicViewSet(viewsets.ModelViewSet):
    queryset = Music.objects.all()
    serializer_class = MusicSerializer

    def get_permissions(self):
        if self.action == "create":
            return [permissions.IsAuthenticated()]

        if self.action in ["update", "partial_update", "destroy"]:
            return [IsOwnerOrAdmin()]

        return [permissions.AllowAny()]


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer

    def get_queryset(self):
        queryset = (
            Post.objects
            .select_related("author")
            .prefetch_related("likes", "saved", "comments", "reposts")
            .order_by("-created_at")
        )

        saved = self.request.query_params.get("saved")
        if saved == 'true':
            queryset = queryset.filter(saved=self.request.user)

        liked = self.request.query_params.get("liked")
        if liked == 'true':
            queryset = queryset.filter(likes__user=self.request.user)
            
        reposts = self.request.query_params.get("reposts")
        if reposts == 'true':
            queryset = queryset.filter(reposts=self.request.user)

        
        return queryset

    def get_permissions(self):
        if self.action == "create":
            return [permissions.IsAuthenticated()]
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsOwnerOrAdmin()]
        if self.action in ["like_toggle", "save_toggle"]:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    @action(detail=True, methods=["post"])
    def like_toggle(self, request, pk=None):
        post = self.get_object()
        user = request.user

        like = Like.objects.filter(post=post, user=user).first()
        if like:
            like.delete()
            return Response({
                "liked": False,
                "likes_count": post.likes.count()
            }, status=status.HTTP_200_OK)

        Like.objects.create(post=post, user=user)
        return Response({
            "liked": True,
            "likes_count": post.likes.count()
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def save_toggle(self, request, pk=None):
        post = self.get_object()
        user = request.user

        if post.saved.filter(id=user.id).exists():
            post.saved.remove(user)
            return Response({"saved": False, "bookmarks_count": post.saved.count()}, status=status.HTTP_200_OK)

        post.saved.add(user)
        return Response({"saved": True, "bookmarks_count": post.saved.count()}, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=["post"])
    def repost_toggle(self, request, pk=None):
        post = self.get_object()
        user = request.user

        repost = post.reposts.filter(id=user.id).first()

        if repost:
            post.reposts.remove(user)
            return Response({
                "reposted": False,
                "reposts_count": post.reposts.count()
            })

        post.reposts.add(user)

        return Response({
            "reposted": True,
            "reposts_count": post.reposts.count()
        })
        


class StoryViewSet(viewsets.ModelViewSet):
    serializer_class = StorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Story.objects.filter(
            expires_at__gt=timezone.now()
        ).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            expires_at=timezone.now() + timedelta(hours=24)
        )
    

class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['post']

    def get_queryset(self):
        return Comment.objects.select_related("user").order_by("created_at")

    def get_permissions(self):
        if self.action == "create":
            return [permissions.IsAuthenticated()]
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsOwnerOrAdmin()]
        return [permissions.AllowAny()]
    
    @action(detail=True, methods=["post"])
    def like_toggle(self, request, pk=None):
        comment = self.get_object()
        like, created = CommentLike.objects.get_or_create(
            user=request.user,
            comment=comment
        )

        if not created:
            like.delete()
            return Response({"liked": False, "likes_count": comment.likes.count()}, status=status.HTTP_200_OK)

        return Response({"liked": True, "likes_count": comment.likes.count()}, status=status.HTTP_201_CREATED)


class ReplyCommentViewSet(viewsets.ModelViewSet):
    serializer_class = ReplyCommentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['parent_comment']

    def get_queryset(self):
        return ReplyComment.objects.select_related("user").order_by("created_at")

    def get_permissions(self):
        if self.action == "create":
            return [permissions.IsAuthenticated()]
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsOwnerOrAdmin()]
        return [permissions.AllowAny()]
    
    
    @action(detail=True, methods=["post"])
    def like_toggle(self, request, pk=None):
        reply_comment = self.get_object()
        like, created = ReplyCommentLike.objects.get_or_create(
            user=request.user,
            reply_comment=reply_comment
        )

        if not created:
            like.delete()
            return Response({"liked": False, "likes_count": reply_comment.likes.count()}, status=status.HTTP_200_OK)

        return Response({"liked": True, "likes_count": reply_comment.likes.count()}, status=status.HTTP_201_CREATED)
    
    
class FollowingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FollowingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        followed_ids = self.request.user.following.values_list(
            "followed_user_id"
        )

        return (
            Post.objects
            .filter(author_id__in=followed_ids)
            .select_related("author")
            .order_by("-created_at")
        ) 
        
        
        
class FriendViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FriendSerializer   
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        
        followed_ids = self.request.user.following.values_list(
            "followed_user_id"
        )

        follower_ids = self.request.user.followers.values_list(
            "following_user_id"
        )

        return (
            Post.objects
            .filter(author_id__in=followed_ids)
            .filter(author_id__in=follower_ids)
        )
    