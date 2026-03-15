from django.contrib import admin
from .models import UserModel, Follow


@admin.register(UserModel)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "email", "first_name", "last_name", "created_at")
    search_fields = ("username", "email", "first_name", "last_name")
    list_filter = ("created_at",)
    ordering = ("-created_at",)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("id", "following_user", "followed_user", "created_at")
    search_fields = ("following_user__username", "followed_user__username")
    list_filter = ("created_at",)
