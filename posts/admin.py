from django.contrib import admin
from .models import (
    Hashtag,
    Music,
    Post,
    Like,
    Comment,
    CommentLike,
    ReplyComment,
    ReplyCommentLike,
)


@admin.register(Hashtag)
class HashtagAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Music)
class MusicAdmin(admin.ModelAdmin):
    list_display = ("id", "music_name", "music_file")
    search_fields = ("music_name",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "music", "hashtag", "created_at")
    search_fields = ("title", "author__username", "caption")
    list_filter = ("created_at", "music", "hashtag")
    ordering = ("-created_at",)


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "user")
    search_fields = ("post__title", "user__username")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "user", "text", "created_at")
    search_fields = ("text", "user__username", "post__title")
    list_filter = ("created_at",)


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "comment")
    search_fields = ("user__username", "comment__text")


@admin.register(ReplyComment)
class ReplyCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "user", "parent_comment", "text", "created_at")
    search_fields = ("text", "user__username")
    list_filter = ("created_at",)


@admin.register(ReplyCommentLike)
class ReplyCommentLikeAdmin(admin.ModelAdmin):
    list_display = ("id", "reply_comment", "user", "created_at")
    search_fields = ("reply_comment__text", "user__username")
    list_filter = ("created_at",)
