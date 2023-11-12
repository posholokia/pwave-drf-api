from django.urls import path, include
from rest_framework import routers
from .views import *
from rest_framework_simplejwt.views import TokenBlacklistView

router = routers.DefaultRouter()
router.register('users', CustomUserViewSet)

urlpatterns = [
    path('jwt/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('', include('djoser.urls.jwt')),
    path('change_email/', ChangeEmailView.as_view(), name='change_email'),
    path('change_email_confirm/', ChangeEmailConfirmView.as_view(), name='change_email_confirm'),
    path('super/', CreateSuperuser.as_view())
]

urlpatterns += router.urls
