from django.db.models import Avg
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend, OrderingFilter
from rest_framework import filters, generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from api.filters import TitleFilter
from api.permissions import (IsAdminOrReadOnly, IsAdminUser, IsAuthor,
                             IsAuthorOrReadOnly)
from api.serializers import (AdminRegisterSerializer, CategorySerializer,
                             CommentSerializer, GenreSerializer,
                             ReviewSerializer, TitleCreateUpdateSerializer,
                             TitleSerializer, TokenObtainSerializer,
                             UserRegisterSerializer, UserSerializer)
from api_yamdb.settings import DEFAULT_FROM_EMAIL
from reviews.models import Category, Genre, Review, Title, User


class UserRegisterView(APIView):
    """
    Отвечает за регистрацию анонимных
    пользователей и отправку кода на почту.
    """

    def post(self, request):
        """
        Обрабатывает POST-запрос для регистрации пользователя.
        Если пользователь уже существует, отправляет новый код подтверждения.
        """
        user = User.objects.filter(
            username=request.data.get('username')).first()
        if user:
            if user.email != request.data.get('email'):
                return Response(status=status.HTTP_400_BAD_REQUEST)
            user.save()
            subject = 'Ваш код подтверждения'
            message = f'Ваш код подтверждения: {user.confirmation_code}'
            from_email = DEFAULT_FROM_EMAIL
            recipient_list = [user.email]
            send_mail(subject, message, from_email, recipient_list)
            return Response({
                'message': 'User already exists. New confirmation code sent.'
            }, status=status.HTTP_200_OK)
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminRegisterViewSet(viewsets.ModelViewSet):
    """
    Отвечает за возможность админа делать
    различные запросы на адрес /users.
    """

    queryset = User.objects.all()
    serializer_class = AdminRegisterSerializer
    permission_classes = (IsAuthenticated, IsAdminUser)
    http_method_names = ('get', 'post', 'delete', 'patch')
    pagination_class = LimitOffsetPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)

    @action(
        detail=False,
        methods=['get', 'patch', 'delete'],
        url_path='(?P<username>[^/.]+)'
    )
    def user_by_username(self, request, username=None):
        if request.method == 'GET':
            user = get_object_or_404(User, username=username)
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        if request.method == 'DELETE':
            user = get_object_or_404(User, username=username)
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            user = get_object_or_404(User, username=username)
            serializer = self.get_serializer(
                user,
                data=request.data,
                partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class TokenObtainView(APIView):
    """Отвечает за работу с токеном(его получение при запросе)."""

    def post(self, request):
        """
        Обрабатывает POST-запрос для получения токена.
        Проверяет код подтверждения и выдает JWT-токен при успешной проверке.
        """
        serializer = TokenObtainSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        confirmation_code = serializer.validated_data['confirmation_code']
        user = get_object_or_404(User, username=username)
        # Проверка кода подтверждения
        if user.confirmation_code != confirmation_code:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        refresh = RefreshToken.for_user(user)
        return Response({
            'token': str(refresh.access_token)
        }, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Отвечает за получение и обновление профиля пользователя."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class CategoryViewSet(viewsets.ModelViewSet):
    """Представление для управления категориями."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ('name',)
    http_method_names = ('get', 'post', 'delete', 'patch')
    permission_classes = [IsAuthenticatedOrReadOnly, IsAdminOrReadOnly]

    @action(
        detail=False,
        methods=['delete', 'patch'],
        url_path='(?P<slug>[^/.]+)',
        permission_classes=[IsAuthenticated, IsAdminUser]
    )
    def delete_category_by_slug(self, request, slug=None):
        if request.method == 'DELETE':
            category = get_object_or_404(Category, slug=slug)
            category.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class GenreViewSet(viewsets.ModelViewSet):
    """Представление для управления жанрами."""

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = (filters.SearchFilter, DjangoFilterBackend,)
    search_fields = ('name',)
    permission_classes = [IsAuthenticatedOrReadOnly, IsAdminOrReadOnly]
    http_method_names = ('get', 'post', 'delete', 'patch')

    @action(
        detail=False,
        methods=['delete', 'get'],
        url_path='(?P<slug>[^/.]+)',
        permission_classes=[IsAuthenticated, IsAdminUser]
    )
    def delete_genre_by_slug(self, request, slug=None):
        if request.method == 'DELETE':
            genre = get_object_or_404(Genre, slug=slug)
            genre.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class TitleViewSet(viewsets.ModelViewSet):
    """Представление для управления произведениями."""

    serializer_class = TitleSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsAdminOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter
    http_method_names = ('get', 'post', 'delete', 'patch')

    def get_queryset(self):
        queryset = Title.objects.all()
        return queryset.annotate(rating=Avg('reviews__score'))

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return TitleCreateUpdateSerializer
        return TitleSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """Представление для управления отзывами."""

    serializer_class = ReviewSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    http_method_names = ('get', 'post', 'delete', 'patch')

    def get_queryset(self):
        return get_object_or_404(
            Title, id=self.kwargs.get('title_id')).reviews.all()

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            title=get_object_or_404(Title, id=self.kwargs.get('title_id'))
        )


class CommentViewSet(viewsets.ModelViewSet):
    """Представление для управления комментариями к отзывам."""

    serializer_class = CommentSerializer
    http_method_names = ('get', 'post', 'delete', 'patch')
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthor)

    def get_review(self):
        return get_object_or_404(
            Review,
            id=self.kwargs.get('review_id'),
            title_id=self.kwargs.get('title_id')
        )

    def get_queryset(self):
        return self.get_review().comments.all()

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            review=self.get_review()
        )
