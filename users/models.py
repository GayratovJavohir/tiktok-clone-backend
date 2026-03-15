from django.db import models
from django.contrib.auth.models import AbstractUser


class UserModel(AbstractUser):
    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    pronoun = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_private = models.BooleanField(default=False)

    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username


class Follow(models.Model):
    following_user = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, related_name='following'
    )
    followed_user = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, related_name='followers'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('following_user', 'followed_user')

    def __str__(self):
        return f"{self.following_user} → {self.followed_user}"
