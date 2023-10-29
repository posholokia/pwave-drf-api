"""
Этот файл содержит дополнения и исправления схемы генерации OpenAPI
документации библиотеки drf-spectacular.
"""

from drf_spectacular.extensions import OpenApiViewExtension
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class Fix1(OpenApiViewExtension):
    """
    Дополнение описания эндпоинтов авторизации.
    """
    target_class = 'taskmanager.views.CustomUserViewSet'

    def view_replacement(self):
        @extend_schema_view(list=extend_schema(description='Запрос от юзера: данные юзера.\n\n'
                                                           'Запрос от админа: список всех пользователей.'),
                            create=extend_schema(description='Создать пользователя'),
                            )
        class Fixed(self.target_class):
            @extend_schema(description='Эндпоинт для активация аккаунта пользователя. '
                                       'Необходимо получить uid и token из ссылки по которой перешел пользователь: '
                                       '/auth/activate/{uid}/{token}',
                           responses=TokenObtainPairSerializer,
                           )
            def activation(self, request, *args, **kwargs):
                return super().activation(request, *args, **kwargs)

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

        return Fixed


class Fix3(OpenApiViewExtension):
    """
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
    Описаие к эндпоинту проверки JWT access и resfresh токенов.
    """
    target_class = 'rest_framework_simplejwt.views.TokenVerifyView'

    def view_replacement(self):
        class Fixed(self.target_class):
            """Проверка действительности JWT токена (как access так и refresh). Оба токена передаются без префикса."""
            pass

        return Fixed


class Fix5(OpenApiViewExtension):
    """
    Описаие эндпоинта создания блокировки JWT токенов.
    """
    target_class = 'rest_framework_simplejwt.views.TokenBlacklistView'

    def view_replacement(self):
        class Fixed(self.target_class):
            """
            Добавление refresh токена в черный список до истечения его действия.
            """
            pass

        return Fixed


def user_me_postprocessing_hook(result, generator, request, public):
    """
    В OpenAPI нет схемы для request запроса метода DELETE, в этом хуке добавлена схема для метода DELETE
    и разделены описания для каждого метода эндпоинтов "/users/me/" и "/users/{id}/"
    """
    request_delete_schema = {
        'requestBody': {
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'required': ['current_password'],
                        'properties': {
                            'current_password': {
                                'type': 'string',
                            },
                        },
                    },
                },
                'application/x-www-form-urlencoded': {
                    'schema': {
                        'type': 'object',
                        'required': ['current_password'],
                        'properties': {
                            'current_password': {
                                'type': 'string',
                            },
                        },
                    },
                },
                'multipart/form-data': {
                    'schema': {
                        'type': 'object',
                        'required': ['current_password'],
                        'properties': {
                            'current_password': {
                                'type': 'string',
                            },
                        },
                    },
                }
            },
            'required': True,
        },
    }

    description = {
        'get': {'description': 'Получить данные авторизованного пользователя'},
        'put': {'description': 'Обновить все данные авторизованного пользователя'},
        'patch': {'description': 'Частично обновить данные авторизованного пользователя'},
        'delete': {'description': 'Удалить авторизованного пользователя'},
    }

    methods = ['get', 'put', 'patch', 'delete']
    endpoints = ['/auth/users/me/', '/auth/users/{id}/']

    for endpoint in endpoints:
        for method in methods:
            schema = result['paths'][endpoint][method]
            schema.update(description[method])

            if method == 'delete':
                schema.update(request_delete_schema)

    return result
