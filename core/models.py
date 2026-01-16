from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    avatar = models.ImageField(upload_to="avatars", null=True)
    bio = models.TextField()
    follower_count = models.IntegerField(default=0)
    following_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(max_length=30)

# Create your models here.
class Article(models.Model):
    title = models.CharField(max_length=300)
    content = models.JSONField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    cover_image = models.ImageField(upload_to="article-images", null=True)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True)
    tags = models.ManyToManyField(Tag, related_name="articles")
    created_at = models.DateTimeField(auto_now_add=True)
    likes_count = models.IntegerField(default=0)
    views_count = models.IntegerField(default=0)
    dislikes_count = models.IntegerField(default=0)


class Comment(models.Model):
    text = models.TextField()
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class ArticleReaction(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction = models.CharField(choices=[
        ('like', 'LIKE'),
        ('dislike', 'DISLIKE'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)


class Follow(models.Model):
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name="followings")
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name = 'followers')
    created_at = models.DateTimeField(auto_now_add=True)


class ArticleView(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='viewed_articles')
    anonymous_id = models.CharField()
