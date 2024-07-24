from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import UniqueConstraint


from reviews.managers import UserManager
from reviews.service import generate_confirmation_code
from reviews.validators import validate_username, validate_year
from reviews.constants import (CATEGORY_NAME_MAX_LEN,
                               CONFIRMATION_CODE_MAX_LEN,
                               EMAIL_MAX_LEN,
                               MAX_SCORE,
                               MIN_SCORE,
                               ROLE_MAX_LEN,
                               TEXT_PREVIEW_LEN,
                               TITLE_NAME_MAX_LEN,
                               USERNAME_MAX_LEN,
                               USER,
                               ROLE_CHOICES)


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
        ],
        verbose_name='Имя пользователя'
    )
    email = models.EmailField(
        max_length=EMAIL_MAX_LEN,
        unique=True,
        verbose_name='Электронная почта'
    )
    confirmation_code = models.CharField(
        max_length=CONFIRMATION_CODE_MAX_LEN,
        blank=True,
        null=True,
        verbose_name='Код подтверждения'
    )
    bio = models.TextField(blank=True, verbose_name='Биография')
    role = models.CharField(
        max_length=ROLE_MAX_LEN,
        choices=ROLE_CHOICES,
        default=USER,
        verbose_name='Роль'
    )
    objects = UserManager()

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        if not self.confirmation_code:
            self.confirmation_code = generate_confirmation_code()
        super(User, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)


class AbstractNameSlug(models.Model):
    """Абстрактная модель для с полями 'name' и 'slug'."""
    name = models.CharField(
        max_length=CATEGORY_NAME_MAX_LEN, verbose_name='Название'
    )
    slug = models.SlugField(
        unique=True, verbose_name='Уникальный идентификатор'
    )

    class Meta:
        abstract = True
        ordering = ('name',)

    def __str__(self):
        return self.name


class Category(AbstractNameSlug):
    """Модель категории с уникальным именем и слагом."""

    class Meta(AbstractNameSlug.Meta):
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'


class Genre(AbstractNameSlug):
    """Модель жанра с уникальным именем и слагом."""

    class Meta(AbstractNameSlug.Meta):
        verbose_name = 'жанр'
        verbose_name_plural = 'Жанры'


class Title(models.Model):
    """Модель произведения, связанная с категорией и жанрами."""

    name = models.CharField(
        max_length=TITLE_NAME_MAX_LEN, verbose_name='Название'
    )
    year = models.PositiveSmallIntegerField(
        validators=[validate_year], verbose_name='Год'
    )
    description = models.TextField(blank=True, verbose_name='Описание')
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория'
    )
    genre = models.ManyToManyField(Genre, blank=False, verbose_name='Жанр')

    def calculate_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return reviews.aggregate(models.Avg('score'))['score__avg']
        return None

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'произведение'
        verbose_name_plural = 'Произведения'
        default_related_name = 'titles'
        ordering = ('name',)


class AbstractReviewComment(models.Model):
    """Абстрактная модель для отзывов и комментариев."""

    text = models.TextField(verbose_name='Текст')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата публикации'
    )

    class Meta:
        abstract = True
        ordering = ('pub_date',)

    def __str__(self):
        return self.text[:TEXT_PREVIEW_LEN]


class Review(AbstractReviewComment):
    """
    Модель отзыва, связанная с произведением и пользователем (автором),
    с каскадным удалением отзывов при удалении произведения или пользователя.
    """

    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        verbose_name='Произведение'
    )
    score = models.PositiveSmallIntegerField(
        validators=[
            MaxValueValidator(MAX_SCORE),
            MinValueValidator(MIN_SCORE)
        ],
        verbose_name='Оценка'
    )

    class Meta(AbstractReviewComment.Meta):
        constraints = [
            UniqueConstraint(
                fields=['title', 'author'], name='unique_title_author'
            )
        ]
        default_related_name = 'reviews'
        verbose_name = 'отзыв'
        verbose_name_plural = 'Отзывы'


class Comment(AbstractReviewComment):
    """
    Модель комментария, связанная с отзывом и пользователем (автором),
    с каскадным удалением комментариев при удалении отзыва или пользователя.
    """

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        verbose_name='Отзыв'
    )

    class Meta(AbstractReviewComment.Meta):
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        default_related_name = 'comments'
