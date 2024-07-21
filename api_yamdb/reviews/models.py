from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import UniqueConstraint

from reviews.service import generate_confirmation_code
from reviews.managers import UserManager
from reviews.validators import validate_username

FIRST_LETTERS_AMOUNT = 20
USERNAME_MAX_LEN = 150
USER = 'user'
ADMIN = 'admin'
MODERATOR = 'moderator'
ROLE_CHOICES = (
    (USER, 'User'),
    (MODERATOR, 'Moderator'),
    (ADMIN, 'Admin'),
)


class User(AbstractUser):
    """Кастомная модель пользователя, наследуемая от AbstractUser."""

    username = models.CharField(
        max_length=USERNAME_MAX_LEN,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message='Username must be 150 characters or fewer. '
                        'Letters, digits and @/./+/-/_ only.'
            ),
            validate_username
        ]
    )
    email = models.EmailField(
        max_length=254,
        unique=True
    )
    confirmation_code = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True)
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=USER
    )
    objects = UserManager()

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        if not self.confirmation_code:
            self.confirmation_code = generate_confirmation_code()
        super(User, self).save(*args, **kwargs)


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
    year = models.PositiveSmallIntegerField()
    description = models.TextField(blank=True)
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

    rating = models.FloatField(null=True, blank=True)

    def update_rating(self):
        new_rating = self.calculate_rating()
        if new_rating != self.rating:
            self.rating = new_rating
            super().save(update_fields=['rating'])

    def calculate_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return reviews.aggregate(models.Avg('score'))['score__avg']
        return None

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
    score = models.PositiveSmallIntegerField(
        validators=[
            MaxValueValidator(10),
            MinValueValidator(1)
        ]
    )
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['title', 'author'], name='unique_title_author')
        ]

    def __str__(self):
        return self.text[:FIRST_LETTERS_AMOUNT]


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
        return self.text[:FIRST_LETTERS_AMOUNT]
