from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework import filters
from rest_framework.decorators import action
from reviews.models import Category, User, Genre, Review, Title
from rest_framework.pagination import LimitOffsetPagination
from rest_framework import generics, permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from rest_framework.permissions import (IsAuthenticatedOrReadOnly,
                                        IsAuthenticated)

from api_yamdb.settings import DEFAULT_FROM_EMAIL
from api.filters import TitleFilter
from api.permissions import (IsAdminUser, IsAdminOrReadOnly,
                             IsAuthorOrReadOnly, IsAuthor)
from api.serializers import (CategorySerializer, CommentSerializer,
                             UserSerializer, GenreSerializer,
                             ReviewSerializer, TitleSerializer,
                             UserRegisterSerializer, TokenObtainSerializer,
                             AdminRegisterSerializer,
                             TitleCreateUpdateSerializer)


class UserRegisterView(APIView):
    """Отвечает за регистрацию анонимных
    пользователей и отправку кода на почту"""
    def post(self, request):
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
    """Отвечает за возможность админа делать
     различные запросы на адрес /users.
    """
    permission_classes = (IsAuthenticated, IsAdminUser)
    pagination_class = LimitOffsetPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)
    serializer_class = AdminRegisterSerializer
    queryset = User.objects.all()

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
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class CategoryViewSet(viewsets.ModelViewSet):
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
    queryset = Title.objects.all()
    serializer_class = TitleSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsAdminOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter
    http_method_names = ('get', 'post', 'delete', 'patch')

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:
            return TitleCreateUpdateSerializer
        return TitleSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    http_method_names = ('get', 'post', 'delete', 'patch')

    def get_queryset(self):
        title_id = self.kwargs.get('title_id')
        review = Review.objects.filter(title_id=title_id)
        if len(review) == 0:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return review

    def perform_create(self, serializer):
        title_id = self.kwargs.get('title_id')
        title = get_object_or_404(Title, id=title_id)
        author = self.request.user
        serializer.save(author=author, title=title)
        title.update_rating()


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    http_method_names = ('get', 'post', 'delete', 'patch')
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthor)

    def get_queryset(self):
        review_id = self.kwargs.get('review_id')
        title_id = self.kwargs.get('title_id')
        return get_object_or_404(
            Review,
            id=review_id,
            title_id=title_id
        ).comments.all()

    def perform_create(self, serializer):
        review_id = self.kwargs.get('review_id')
        title_id = self.kwargs.get('title_id')
        review = get_object_or_404(Review, id=review_id, title_id=title_id)
        serializer.save(author=self.request.user, review=review)
