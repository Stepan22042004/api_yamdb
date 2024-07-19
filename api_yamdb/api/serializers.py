from rest_framework import serializers
from reviews.models import Category, Genre, Title, Review, Comment, CustomUser
from django.utils import timezone
from django.core.mail import send_mail

from api_yamdb.settings import DEFAULT_FROM_EMAIL


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('email', 'username')

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
        )
        subject = 'Ваш код подтверждения'
        message = f'Ваш код подтверждения: {user.confirmation_code}'
        from_email = DEFAULT_FROM_EMAIL
        recipient_list = [user.email]
        send_mail(subject, message, from_email, recipient_list)
        return user

    def validate_username(self, value):
        if value == 'me':
            raise serializers.ValidationError(
                'Недопустимое имя'
            )
        return value


class AdminRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role',
                  'bio', 'first_name', 'last_name']

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        user.save()
        return user

    def validate_first_name(self, value):
        if len(value) > 150:
            raise serializers.ValidationError(
                'Длина имени более 150 символов'
            )
        return value

    def validate_last_name(self, value):
        if len(value) > 150:
            raise serializers.ValidationError(
                'Длина фамилии более 150 символов'
            )
        return value


class TokenObtainSerializer(serializers.Serializer):
    username = serializers.CharField()
    confirmation_code = serializers.CharField()


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email',
                  'first_name', 'last_name', 'bio', 'role']
        read_only_fields = ['id', 'role']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name', 'slug']


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['name', 'slug']


class TitleSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(many=True, read_only=True)

    class Meta:
        model = Title
        fields = ['id', 'name', 'year', 'description', 'category', 'genre', 'rating']

    def validate_year(self, value):
        current_year = timezone.now().year
        if value > current_year:
            raise serializers.ValidationError(
                'Год выпуска не может быть больше текущего года.'
            )
        return value

    def validate_category(self, value):
        if value is None:
            raise serializers.ValidationError("Добавьте категорию.")
        return value

    def validate_genre(self, value):
        if not value:
            raise serializers.ValidationError("Добавьте жанр.")
        return value


class TitleCreateUpdateSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all()
    )

    genre = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Genre.objects.all(),
        many=True
    )

    class Meta:
        model = Title
        fields = ['id', 'name', 'year', 'description', 'category', 'genre', 'rating']

    def validate_year(self, value):
        current_year = timezone.now().year
        if value > current_year:
            raise serializers.ValidationError(
                'Год выпуска не может быть больше текущего года.'
            )
        return value

    def validate_category(self, value):
        if value is None:
            raise serializers.ValidationError("Добавьте категорию.")
        return value

    def validate_genre(self, value):
        if not value:
            raise serializers.ValidationError("Добавьте жанр.")
        return value

    def validate_name(self, value):
        if len(value) > 256:
            raise serializers.ValidationError('Название произведения не может быть длиннее 256 символов.')
        return value


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    title = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'title', 'text', 'author', 'score', 'pub_date']

    def validate_score(self, value):
        if value < 1 or value > 10:
            raise serializers.ValidationError("Оценка должна быть от 1 до 10.")
        return value


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    review = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'review', 'text', 'author', 'pub_date']
