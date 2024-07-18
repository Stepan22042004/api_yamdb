import random
import string

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator, EmailValidator
from django.contrib.auth.models import PermissionsMixin


def generate_confirmation_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


class CustomUserManager(BaseUserManager):
    '''Менеджер для кастомного пользователя'''

    def create_user(self, email, username, password=None, **extra_fields):
        '''Создание обычного пользователя'''
        if not email:
            raise ValueError('Email поле должно быть заполнено')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        extra_fields.setdefault('is_staff', False)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        '''Создание суперпользователя'''
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперюзер должен иметь is_superuser=True')

        return self.create_user(email, username, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Кастомная модель пользователя, наследуемая от AbstractUser."""

    ROLE_CHOICES = (
        ('user', 'User'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin'),
        ('superuser', 'Superuser'),

    )

    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message='Username must be 150 characters or fewer. '
                        'Letters, digits and @/./+/-/_ only.'
            )
        ]
    )
    email = models.EmailField(
        max_length=254,
        unique=True,
        validators=[EmailValidator()]
    )
    confirmation_code = models.CharField(max_length=100, blank=True, null=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='user'
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    objects = CustomUserManager()

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        if not self.confirmation_code:
            self.confirmation_code = generate_confirmation_code()
        super(CustomUser, self).save(*args, **kwargs)


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
