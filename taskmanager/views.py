from rest_framework import generics
from django.contrib.auth import get_user_model
from djoser.views import UserViewSet

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    """
    Вьюсет на базе вьюсета библиотеки Djoser.
    Здесь переопределены методы, которые не используются с текущей моделью User, чтобы сделать их недоступными.
    """
    def set_username(self, request, *args, **kwargs):
        pass

    def reset_username(self, request, *args, **kwargs):
        pass

    def reset_username_confirm(self, request, *args, **kwargs):
        pass
