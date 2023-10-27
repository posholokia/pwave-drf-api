from rest_framework import generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from djoser.serializers import UidAndTokenSerializer
from drf_spectacular.utils import extend_schema

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    """
    Вьюсет на базе вьюсета библиотеки Djoser.
    Часть методов переопределена под требования проекта.
    """
    def get_serializer_class(self):
        if self.action == 'check_link':
            return UidAndTokenSerializer
        return super().get_serializer_class()

    @action(['post'], detail=False)
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

    @extend_schema(description='Проверка действительности ссылки восстановления пароля')
    @action(methods=['post'], detail=False, permission_classes=[permissions.AllowAny])
    def check_link(self, request, *args, **kwargs):
        """
        Проверка что ссылка /{uid}/{token}/ действительна, чтобы при повторном переходе по использованной ссылке
        на фронте сразу вывели сообщение об ошибке, а не после отправки пароля.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

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
