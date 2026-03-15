from django.contrib.auth import authenticate
from rest_framework import serializers

from posts.models import Comment
from posts.serializers import PostSerializer, CommentSerializer
from users.models import UserModel, Follow


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        style={'input_type': "password"},
        write_only=True,
        min_length=8,
        required=True
    )
    avatar = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = UserModel
        fields = ('username', 'password', 'first_name', 'last_name', 'email', 'bio', 'avatar', 'pronoun',)
        extra_kwargs = {
            'password': {'write_only': True},
            'bio': {'required': False, 'allow_blank': True},
            'pronoun': {'required': False, 'allow_blank': True}
        }

    def create(self, validated_data):
        avatar = validated_data.pop('avatar', None)

        user = UserModel.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            **{k: v for k, v in validated_data.items() if k not in ['username', 'password']}
        )

        if avatar:
            user.avatar = avatar

        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])

        if user and user.is_active:
            return user

        raise serializers.ValidationError('Incorrect username or password')


class UserModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ('id', 'username', 'first_name', 'last_name', 'is_private', 'avatar')


class ProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False, allow_null=True)
    posts = serializers.SerializerMethodField()
    followers = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()

    class Meta:
        model = UserModel
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'bio',
            'pronoun',
            'is_private',
            'posts',
            'comments',
            'is_following',
            'followers',
        )

    def get_posts(self, obj):
        if obj.posts:
            qs = obj.posts.all()
            return PostSerializer(qs, many=True).data
        return None

    def get_comments(self, obj):
        if obj.posts:
            qs = Comment.objects.filter(post__author=obj)

            return CommentSerializer(qs, many=True).data
            # return Comment.objects.filter(post__author=obj).order_by('-created_at')
        return None

    def get_followers(self, obj):
        return obj.followers.count()

    def get_is_following(self, obj):
        request = self.context.get('request')

        if not request or not request.user.is_authenticated:
            return False

        if request.user == obj:
            return False

        return Follow.objects.filter(
            following_user=request.user,
            followed_user=obj
        ).exists()
