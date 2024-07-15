from rest_framework import routers
from django.urls import include, path


router = routers.DefaultRouter()


urlpatterns = [
    path('v1/', include(router.urls)),
]
