from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (AdminRegisterViewSet, CategoryViewSet, CommentViewSet,
                       GenreViewSet, ReviewViewSet, TitleViewSet,
                       TokenObtainView, UserProfileView, UserRegisterView)

router_v1 = DefaultRouter()
router_v1.register('users', AdminRegisterViewSet, basename='users')
router_v1.register('categories', CategoryViewSet, basename='category')
router_v1.register('genres', GenreViewSet, basename='genre')
router_v1.register('titles', TitleViewSet, basename='title')
router_v1.register(
    r'titles/(?P<title_id>\d+)/reviews',
    ReviewViewSet,
    basename='review'
)
router_v1.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentViewSet,
    basename='comment'
)

api_v1_auth_urls = [
    path('signup/', UserRegisterView.as_view(), name='signup'),
    path('token/', TokenObtainView.as_view(), name='token_obtain')
]

urlpatterns = [
    path('v1/users/me/', UserProfileView.as_view(), name='user-profile'),
    path('v1/auth/', include(api_v1_auth_urls)),
    path('v1/', include(router_v1.urls))
]
