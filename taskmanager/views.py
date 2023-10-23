from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model

from djoser.views import UserViewSet

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    """
    Вьюсет на базе вьюсета библиотеки Djoser.
    Часть методов переопределена под требования проекта.
    """

    @action(["post"], detail=False)
    def activation(self, request, *args, **kwargs):
        """
        Метод активации учетной записи пользователя.
        В качестве ответа возвращаются JWT токены, чтобы юзер сразу был авторизован после активации.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user

        super().activation(request, *args, **kwargs)

        refresh = RefreshToken.for_user(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)

    def set_username(self, request, *args, **kwargs):
        """
        Метод не используется.
        """
        pass

    def reset_username(self, request, *args, **kwargs):
        """
        Метод не используется.
        """
        pass

    def reset_username_confirm(self, request, *args, **kwargs):
        """
        Метод не используется.
        """
        pass
