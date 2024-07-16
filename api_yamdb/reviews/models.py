from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class CustomUser(AbstractUser):
    """Кастомная модель пользователя, наследуемая от AbstractUser."""

    bio = models.TextField(blank=True)
    role = models.CharField(max_length=50, default='user')

    def __str__(self):
        return self.username


class Category(models.Model):
    """Модель категории с уникальным именем и слагом."""

    name = models.CharField(max_length=256)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Genre(models.Model):
    """Модель жанра с уникальным именем и слагом."""

    name = models.CharField(max_length=256)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Title(models.Model):
    """Модель произведения, связанная с категорией и жанрами."""

    name = models.CharField(max_length=256)
    year = models.IntegerField()
    description = models.TextField()
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        related_name='titles'
    )
    genre = models.ManyToManyField(
        Genre,
        blank=False,
        related_name='titles'
    )

    def __str__(self):
        return self.name


class Review(models.Model):
    """
    Модель отзыва, связанная с произведением и пользователем (автором),
    с каскадным удалением отзывов при удалении произведения или пользователя.
    """

    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    text = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    score = models.IntegerField()
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['title', 'author']

    def __str__(self):
        return self.text[:20]


class Comment(models.Model):
    """
    Модель комментария, связанная с отзывом и пользователем (автором),
    с каскадным удалением комментариев при удалении отзыва или пользователя.
    """
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    pub_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text[:20]
