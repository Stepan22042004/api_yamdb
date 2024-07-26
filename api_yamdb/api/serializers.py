from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import serializers

from api.constants import FORBIDDEN_NAME, MAX_SCORE, MIN_SCORE
from reviews.models import Category, Comment, Genre, Review, Title, User


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'username')

    def create(self, validated_data):
        user, _ = User.objects.get_or_create(
            email=validated_data['email'],
            username=validated_data['username'],
        )
        subject = 'Ваш код подтверждения'
        message = f'Ваш код подтверждения: {user.confirmation_code}'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = (user.email,)
        send_mail(subject, message, from_email, recipient_list)
        return user

    def validate_username(self, value):
        if value == FORBIDDEN_NAME:
            raise serializers.ValidationError(
                'Недопустимое имя'
            )
        return value


class AdminRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        lookup_field = 'username'
        fields = ('username', 'email', 'role',
                  'bio', 'first_name', 'last_name')


class TokenObtainSerializer(serializers.Serializer):
    username = serializers.CharField()
    confirmation_code = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email',
                  'first_name', 'last_name', 'bio', 'role')
        read_only_fields = ('role',)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        lookup_field = 'slug'
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        lookup_field = 'slug'
        fields = ('name', 'slug')


class TitleSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(many=True, read_only=True)
    rating = serializers.IntegerField(
        read_only=True, default=None
    )

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'description',
                  'category', 'genre', 'rating')


class TitleCreateUpdateSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all()
    )

    genre = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Genre.objects.all(),
        many=True,
        required=True,
        allow_empty=False,
        allow_null=True
    )

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'description',
                  'category', 'genre')

    def validate_year(self, value):
        current_year = timezone.now().year
        if value > current_year:
            raise serializers.ValidationError(
                'Год выпуска не может быть больше текущего года.'
            )
        return value

    def to_representation(self, instance):
        return TitleSerializer(instance).data


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'score', 'pub_date')

    def validate_score(self, value):
        if not (MIN_SCORE <= value <= MAX_SCORE):
            raise serializers.ValidationError(
                f'Оценка должна быть от {MIN_SCORE} до {MAX_SCORE}.'
            )
        return value

    def validate(self, data):
        request = self.context.get('request')
        title_id = self.context.get('view').kwargs.get('title_id')

        if request and request.method == 'POST':
            if Review.objects.filter(
                title_id=title_id,
                author=request.user
            ).exists():
                raise serializers.ValidationError('Уже оставили отзыв.')
        return data


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')
