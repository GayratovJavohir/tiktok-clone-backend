from django.db import models
from users.models import UserModel
from django.core.validators import FileExtensionValidator


class Hashtag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Music(models.Model):
    music_name = models.CharField(max_length=200)
    music_file = models.FileField(upload_to='music/', validators=[FileExtensionValidator(allowed_extensions=["mp3", "aac", "wav", "flac", "ogg", "m4a"])])
    author = models.ForeignKey(UserModel, on_delete=models.CASCADE, null=True, blank=True, related_name='musics')

    def __str__(self):
        return self.music_name


class Post(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='posts/images/', blank=True, null=True)
    video = models.FileField(upload_to='posts/videos/', blank=True, null=True)
    caption = models.TextField(blank=True, null=True)
    author = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='posts')
    music = models.ForeignKey(Music, on_delete=models.SET_NULL, null=True, blank=True)
    hashtag = models.ForeignKey(Hashtag, on_delete=models.SET_NULL, null=True, blank=True)
    saved = models.ManyToManyField(UserModel, blank=True, null=True, related_name='saved')
    reposts = models.ManyToManyField(UserModel, blank=True, null=True, related_name='reposted_posts')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author.username} - {self.title}"
    
    
class Story(models.Model):
    author = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="stories/", null=True, blank=True)
    video = models.FileField(upload_to="stories/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()



class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='post_likes')

    class Meta:
        unique_together = ('post', 'user')

    def __str__(self):
        return f"{self.user.username} liked {self.post.id}"


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='comments/images/', blank=True, null=True)
    gif = models.FileField(upload_to='comments/gifs/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username}"


class CommentLike(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='comment_likes')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')

    class Meta:
        unique_together = ('user', 'comment')

    def __str__(self):
        return f"{self.user.username} liked comment {self.comment.id}"


class ReplyComment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reply_comments')
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='reply_comments')

    parent_comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='replies',
        null=True,
        blank=True
    )

    parent_reply = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='child_replies',
        null=True,
        blank=True
    )

    text = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='replies/images/', blank=True, null=True)
    gif = models.FileField(upload_to='replies/gifs/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply by {self.user.username}"



class ReplyCommentLike(models.Model):
    reply_comment = models.ForeignKey(
        ReplyComment, on_delete=models.CASCADE, related_name='likes' 
    )
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='reply_comment_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('reply_comment', 'user')

    def __str__(self):
        return f"{self.user.username} liked reply {self.reply_comment.id}"
