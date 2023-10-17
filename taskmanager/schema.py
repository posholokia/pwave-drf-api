from drf_spectacular.extensions import OpenApiViewExtension
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.decorators import action


class Fix1(OpenApiViewExtension):
    """
    Добавление описания к API документации библиотеки Djoser.
    Описаие добавлено к эндпоинтам модели User.
    """
    target_class = 'taskmanager.views.CustomUserViewSet'

    def view_replacement(self):
        @extend_schema_view(list=extend_schema(description='Список всех пользователей'),
                            create=extend_schema(description='Создать пользователя'),
                            retrieve=extend_schema(description='Получить данные пользователя по id'),
                            update=extend_schema(description='Обновить все данные пользователя по id'),
                            partial_update=extend_schema(description='Частично обновить данные пользователя по id'),
                            destroy=extend_schema(description='Удалить пользователя по id'),
                            )
        class Fixed(self.target_class):
            @extend_schema(description='Эндпоинт для активация аккаунта пользователя. '
                                       'Необходимо получить uid и token из ссылки по которой перешел пользователь: '
                                       '/auth/activate/{uid}/{token}')
            def activation(self, request, *args, **kwargs):
                return super().activation(request, *args, **kwargs)

            @extend_schema(description=
                           'get: Получить данные пользователя\n\n'
                           'put: Обновить все данные пользователя\n\n'
                           'patch: Частично обновить данные пользователя\n\n'
                           'delete: Удалить пользователя\n\n'
                           'Пользователь определяется по токену.')
            def me(self, request, *args, **kwargs):
                return super().me(request, *args, **kwargs)

            @extend_schema(description='Повторная отправка письма с ссылкой для активации аккаунта.')
            def resend_activation(self, request, *args, **kwargs):
                return super().resend_activation(request, *args, **kwargs)

            @extend_schema(description='Установить новый пароль. Используется в личном кабинете после авторизации.')
            def set_password(self, request, *args, **kwargs):
                return super().set_password(request, *args, **kwargs)

            @extend_schema(description='Сброс пароля. '
                                       'Используется на экране входа, если пользователь забыл свой пароль. '
                                       'Пользователю отправится письмо с ссылкой подтверждения.')
            def reset_password(self, request, *args, **kwargs):
                return super().reset_password(request, *args, **kwargs)

            @extend_schema(description='Подтверждение сброса пароля. Когда пользователь переходит по ссылке '
                                       'auth/password/reset/confirm/{uid}/{token}')
            def reset_password_confirm(self, request, *args, **kwargs):
                return super().reset_password_confirm(request, *args, **kwargs)

            @extend_schema(description='Не используется. \n\nСмена логина.')
            def set_username(self, request, *args, **kwargs):
                return super().set_username(request, *args, **kwargs)

            @extend_schema(description='Не используется.\n\nСброс логина.')
            def reset_username(self, request, *args, **kwargs):
                return super().reset_username(request, *args, **kwargs)

            @extend_schema(description='Не используется.\n\nПодтверждение сброса логина.')
            def reset_username_confirm(self, request, *args, **kwargs):
                return super().reset_username_confirm(request, *args, **kwargs)

        return Fixed


class Fix2(OpenApiViewExtension):
    """
    Добавление описания к API документации библиотеки Djoser.
    Описаие эндпоинту создания JWT токенов.
    """
    target_class = 'rest_framework_simplejwt.views.TokenObtainPairView'

    def view_replacement(self):
        class Fixed(self.target_class):
            """Создает пару JWT токенов: access_token и refresh_token.\n\n
            Для авторизации access_token всегда передается с префиксом "JWT" через пробел, например: \n\n
            "JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjk1MTM5MTYzLCJpYXQiO"
            """
            pass

        return Fixed


class Fix3(OpenApiViewExtension):
    """
    Добавление описания к API документации библиотеки Djoser.
    Описаие к эндпоинту обновления JWT access токена.
    """
    target_class = 'rest_framework_simplejwt.views.TokenRefreshView'

    def view_replacement(self):
        class Fixed(self.target_class):
            """Обновление JWT access_token."""
            pass

        return Fixed


class Fix4(OpenApiViewExtension):
    """
    Добавление описания к API документации библиотеки Djoser.
    Описаие к эндпоинту проверки JWT access и resfresh токенов.
    """
    target_class = 'rest_framework_simplejwt.views.TokenVerifyView'

    def view_replacement(self):
        class Fixed(self.target_class):
            """Проверка действительности JWT токена (как access так и refresh). Оба токена передаются без префикса."""
            pass

        return Fixed
