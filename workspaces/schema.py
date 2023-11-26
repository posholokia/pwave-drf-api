"""
Этот файл содержит дополнения и исправления схемы генерации OpenAPI
документации библиотеки drf-spectacular.
"""

from drf_spectacular.extensions import OpenApiViewExtension
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class Fix1(OpenApiViewExtension):
    target_class = 'workspaces.views.UserList'

    def view_replacement(self):
        class Fixed(self.target_class):
            """Список всех пользователей для поиска.\n\n
               Поиск ведется по почте, начало передается через query параметр users.\n\n
               Например: /api/user_list/?users=foobar\n\n
               Можно передать дополнительный параметр workspace для исклчения юзеров, уже
               приглашенных/присутствующих в этом РП: /api/user_list/?users=foo&workspace=17"""
            pass

        return Fixed
