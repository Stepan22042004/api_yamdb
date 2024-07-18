from rest_framework import viewsets, status, mixins
from rest_framework.views import APIView
from rest_framework import filters
from rest_framework.permissions import (IsAuthenticatedOrReadOnly,
                                        IsAuthenticated)
from reviews.models import Category, Comment, CustomUser, Genre, Review, Title
from rest_framework.pagination import LimitOffsetPagination
from rest_framework import generics, permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from rest_framework.exceptions import NotFound

from reviews.models import generate_confirmation_code
from api_yamdb.settings import DEFAULT_FROM_EMAIL
from .permissions import IsAdminUser
from .serializers import (CategorySerializer, CommentSerializer,
                          CustomUserSerializer, GenreSerializer,
                          ReviewSerializer, TitleSerializer,
                          UserRegisterSerializer, TokenObtainSerializer,
                          AdminRegisterSerializer, TitleCreateUpdateSerializer)


class UserRegisterView(APIView):
    """Отвечает за регистрацию анонимных
    пользователей и отправку кода на почту"""
    def post(self, request):
        user = CustomUser.objects.filter(
            username=request.data.get('username')).first()
        if user:
            if user.email != request.data.get('email'):
                return Response(status=status.HTTP_400_BAD_REQUEST)
            user.confirmation_code = generate_confirmation_code()

            subject = 'Ваш код подтверждения'
            message = f'Ваш код подтверждения: {user.confirmation_code}'
            from_email = DEFAULT_FROM_EMAIL
            recipient_list = [user.email]
            send_mail(subject, message, from_email, recipient_list)
            return Response({
                'message': 'User already exists. New confirmation code sent.'
            }, status=status.HTTP_200_OK)
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminRegisterViewSet(viewsets.ViewSet):
    """Отвечает за возможность админа делать
    различные запросы на адрес /users"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = LimitOffsetPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)

    def create(self, request):
        serializer = AdminRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        queryset = CustomUser.objects.all()
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = AdminRegisterSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        serializer = AdminRegisterSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        try:
            user = CustomUser.objects.get(username=pk)
            serializer = AdminRegisterSerializer(user)
            return Response(serializer.data)
        except CustomUser.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def partial_update(self, request, pk=None):
        try:
            user = CustomUser.objects.get(username=pk)
            serializer = AdminRegisterSerializer(user, data=request.data,
                                                 partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):  # Обработка DELETE запросов
        try:
            user = CustomUser.objects.get(username=pk)
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CustomUser.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class TokenObtainView(APIView):
    """Отвечает за работу с токеном(его получение при запросе)"""
    def post(self, request):
        serializer = TokenObtainSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        confirmation_code = serializer.validated_data['confirmation_code']
        user = get_object_or_404(CustomUser, username=username)
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
    serializer_class = CustomUserSerializer

    def get_object(self):
        return self.request.user


class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer


class CategoryViewSet(mixins.ListModelMixin,
                      mixins.CreateModelMixin,
                      mixins.DestroyModelMixin,
                      viewsets.GenericViewSet,
                      ):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ('name',)

    def get_permissions(self):
        if self.action in ['create', 'destroy', 'partial_update', 'update']:
            self.permission_classes = [IsAuthenticatedOrReadOnly, IsAdminUser]
        else:
            self.permission_classes = [IsAuthenticatedOrReadOnly,]
        return super().get_permissions()

    def patch(self, request, *args, **kwargs):
        if request.user.role == 'user':
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        if request.user.role == 'user':
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, pk=None):
        try:
            instance = Category.objects.get(slug=pk)
        except Category.DoesNotExist:
            raise NotFound('Категория не найдена по данному slug')
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ('name',)

    def partial_update(self, request, *args, **kwargs):
        if request.user.role == 'user' or request.user.role == 'moderator':
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            self.permission_classes = [IsAuthenticatedOrReadOnly, IsAdminUser]
        return super().get_permissions()

    def destroy(self, request, pk=None):
        try:
            instance = Genre.objects.get(slug=pk)
        except Genre.DoesNotExist:
            raise NotFound('Категория не найдена по данному slug')
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all()
    serializer_class = TitleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    http_method_names = ['get', 'post', 'patch', 'delete',
                         'head', 'options', 'trace']

    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            self.permission_classes = [IsAuthenticatedOrReadOnly, IsAdminUser]
        return super().get_permissions()

    def partial_update(self, request, *args, **kwargs):
        if request.user.role == 'user' or request.user.role == 'moderator':
            return Response(status=status.HTTP_403_FORBIDDEN)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return TitleCreateUpdateSerializer
        return TitleSerializer


class ReviewViewSet(mixins.ListModelMixin,
                    mixins.CreateModelMixin,
                    mixins.DestroyModelMixin,
                    viewsets.GenericViewSet,
                    mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [
        IsAuthenticatedOrReadOnly,
    ]
    http_method_names = ['get', 'post', 'patch', 'delete',
                         'head', 'options', 'trace']

    def perform_create(self, serializer):
        title_id = self.kwargs.get('title_id')
        title = Title.objects.get(id=title_id)
        serializer.save(author=self.request.user, title=title)

    def partial_update(self, request, *args, **kwargs):
        review = self.get_object()
        if request.user.role == 'user' and review.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        review = self.get_object()
        if request.user.role == 'user' and review.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        return super().destroy(request, *args, **kwargs)

    




class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [
        IsAuthenticatedOrReadOnly,
    ]

    def perform_create(self, serializer):
        review_id = self.kwargs.get('review_id')
        review = Review.objects.get(id=review_id)
        serializer.save(author=self.request.user, review=review)
