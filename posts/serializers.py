from rest_framework import serializers

from posts.models import Hashtag, Music, Post, Story
from users.models import UserModel, Follow
from posts.models import Comment, ReplyComment
from rest_framework import serializers
from .models import Comment, ReplyComment


class HashtagModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = ('id', 'name',)


class MusicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Music
        fields = ('id', 'music_name', 'music_file')


class PostSerializer(serializers.ModelSerializer):
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    bookmarks_count = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    reposts_count = serializers.SerializerMethodField()
    is_reposted = serializers.SerializerMethodField()
    reposted_by_followers = serializers.SerializerMethodField()

    author_id = serializers.PrimaryKeyRelatedField(
        queryset=UserModel.objects.all(),
        write_only=True,
        required=True
    )
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            'id',
            'title',
            'image',
            'video',
            'caption',
            'author_id',
            'author',
            'created_at',
            'likes_count',
            'comments_count',
            'is_liked',
            'is_saved',
            'bookmarks_count',
            'is_reposted',
            'reposts_count',
            "reposted_by_followers",
        )

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_bookmarks_count(self, obj):
        return obj.saved.count()
    
    def get_reposts_count(self, obj):
        return obj.reposts.count()

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.likes.filter(user=request.user).exists()

    def get_is_saved(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.saved.filter(id=request.user.id).exists()
        return False
    
    def get_is_reposted(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.reposts.filter(id=request.user.id).exists()
        return False
    
    def get_reposted_by_followers(self, obj):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return None

        my_follower_ids = Follow.objects.filter(
            followed_user=request.user
        ).values_list("following_user_id", flat=True)

        repost_user = obj.reposts.filter(
            id__in=my_follower_ids
        ).first()

        if repost_user:
            return {
                "id": repost_user.id,
                "username": repost_user.username
            }

        return None



    def get_author(self, obj):
        return {
            "id": obj.author.id,
            "first_name": obj.author.first_name,
            "last_name": obj.author.last_name,
            "avatar": obj.author.avatar.url if obj.author.avatar else None
        }

    def create(self, validated_data):
        author = validated_data.pop("author_id")
        return Post.objects.create(author=author, **validated_data)
    
    

class StorySerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField(read_only=True)

    author_id = serializers.PrimaryKeyRelatedField(
        queryset=UserModel.objects.all(),
        write_only=True,
        required=False,    
        source="author"   
    )

    class Meta:
        model = Story
        fields = "__all__"
        read_only_fields = ["author", "created_at", "expires_at"]

    def get_author(self, obj):
        u = obj.author
        return {
            "id": u.id,
            "username": u.username,
            "avatar": u.avatar.url if getattr(u, "avatar", None) else None
        }



class ReplyCommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    liked_by_me = serializers.SerializerMethodField()

    parent_comment = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.all(),
        write_only=True,
        required=False
    )

    parent_reply = serializers.PrimaryKeyRelatedField(
        queryset=ReplyComment.objects.all(),
        write_only=True,
        required=False
    )

    class Meta:
        model = ReplyComment
        fields = (
            'id',
            'parent_comment',
            'parent_reply',
            'user',
            'text',
            'likes_count',
            'liked_by_me',
            'image',
            'gif',
            'created_at',
        )
        read_only_fields = (
            'id',
            'user',
            'likes_count',
            'liked_by_me',
            'created_at',
        )

    def validate(self, data):
        parent_comment = data.get('parent_comment')
        parent_reply = data.get('parent_reply')

        if not parent_comment and not parent_reply:
            raise serializers.ValidationError(
                "Reply must have parent_comment or parent_reply"
            )

        if parent_comment and parent_reply:
            raise serializers.ValidationError(
                "Reply can have only ONE parent"
            )

        return data

    def create(self, validated_data):
        request = self.context['request']
        user = request.user

        parent_comment = validated_data.pop('parent_comment', None)
        parent_reply = validated_data.pop('parent_reply', None)

        if parent_comment:
            post = parent_comment.post
        else:
            post = parent_reply.post

        reply = ReplyComment.objects.create(
            user=user,
            post=post,
            parent_comment=parent_comment,
            parent_reply=parent_reply,
            **validated_data
        )
        return reply

    def get_user(self, obj):
        return {
            "id": obj.user.id,
            "username": f"{obj.user.first_name} {obj.user.last_name}".strip(),
            "avatar": obj.user.avatar.url if obj.user.avatar else None
        }

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_liked_by_me(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False


class PostMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = (
            'id',
            'title',
            'image',
            'video',
        )


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    liked_by_me = serializers.SerializerMethodField()
    reply_comments = ReplyCommentSerializer(many=True, read_only=True, source='replies')
    post = PostMiniSerializer(read_only=True)
    post_id = serializers.PrimaryKeyRelatedField(
        queryset=Post.objects.all(),
        write_only=True,
        required=True,
        source="post"
        )

    class Meta:
        model = Comment
        fields = (
            'id',
            'post',
            'post_id',
            'user',
            'text',
            'reply_comments',
            'likes_count',
            'liked_by_me',
            'image',
            'gif',
            'created_at',
        )
        read_only_fields = ('created_at', 'user', 'likes_count', 'liked_by_me', 'reply_comments')

    def get_user(self, obj):
        return {
            "id": obj.user.id,
            "username": obj.user.username,
            "avatar": obj.user.avatar.url if obj.user.avatar else None
        }

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_liked_by_me(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    


    
    
class FollowingSerializer(serializers.ModelSerializer):
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    bookmarks_count = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()

    author_id = serializers.PrimaryKeyRelatedField(
        queryset=UserModel.objects.all(),
        write_only=True,
        required=True
    )
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            'id',
            'title',
            'image',
            'video',
            'caption',
            'author_id',
            'author',
            'created_at',
            'likes_count',
            'comments_count',
            'is_liked',
            'is_saved',
            'bookmarks_count',
        )

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_bookmarks_count(self, obj):
        return obj.saved.count()

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.likes.filter(user=request.user).exists()

    def get_is_saved(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.saved.filter(id=request.user.id).exists()
        return False

    def get_author(self, obj):
        return {
            "id": obj.author.id,
            "first_name": obj.author.first_name,
            "last_name": obj.author.last_name,
            "avatar": obj.author.avatar.url if obj.author.avatar else None
        }
        
        
        
class FriendSerializer(serializers.ModelSerializer):
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    bookmarks_count = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()

    author_id = serializers.PrimaryKeyRelatedField(
        queryset=UserModel.objects.all(),
        write_only=True,
        required=True
    )
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            'id',
            'title',
            'image',
            'video',
            'caption',
            'author_id',
            'author',
            'created_at',
            'likes_count',
            'comments_count',
            'is_liked',
            'is_saved',
            'bookmarks_count',
        )

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_bookmarks_count(self, obj):
        return obj.saved.count()

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.likes.filter(user=request.user).exists()

    def get_is_saved(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.saved.filter(id=request.user.id).exists()
        return False

    def get_author(self, obj):
        return {
            "id": obj.author.id,
            "first_name": obj.author.first_name,
            "last_name": obj.author.last_name,
            "avatar": obj.author.avatar.url if obj.author.avatar else None
        }
        