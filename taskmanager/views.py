from rest_framework import generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
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

    def create(self, request, *args, **kwargs):
        """
        Если пользователь уже был создан, но не активирован, возвращаем сообщение, что пользователь
        существует, но не активирован.
        """
        email = request.data.get("email", None)
        user = User.objects.filter(email=email).first()

        if user and not user.is_active:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={'email': ['Пользователь с этим email не активирован']})

        return super().create(request, *args, **kwargs)

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


class CreateTokenPairView(TokenObtainPairView):
    @extend_schema(description=
            ('Создает пару JWT токенов: access_token и refresh_token.\n\n'
            'Для авторизации access_token всегда передается с префиксом "JWT" через пробел, например: \n\n'
            '"JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjk1MTM5MTYzLCJpYXQiO"')
            )
    def post(self, request, *args, **kwargs) -> Response:
        """
        При попытке залогинитсья не активированным пользователем возвращаем сообщение, что пользователь
        существует, но не активирован.
        """
        email = request.data.get('email')
        user = User.objects.filter(email=email).first()

        if user and not user.is_active:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={'email': ['Пользователь с этим email не активирован']})

        return super().post(request, *args, **kwargs)