"""
Этот файл содержит дополнения и исправления схемы генерации OpenAPI
документации библиотеки drf-spectacular.
"""

from drf_spectacular.extensions import OpenApiViewExtension
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes

from workspaces import serializers


class Fix1(OpenApiViewExtension):
    target_class = 'workspaces.views.UserList'

    def view_replacement(self):
        class Fixed(self.target_class):
            """Список всех пользователей для поиска.\n\n
               Поиск ведется по почте, начало передается через query параметр users.\n\n
               Например: /api/user_list/?users=foobar\n\n
               Можно передать дополнительный параметр workspace для исклчения юзеров, уже
               приглашенных/присутствующих в этом РП: /api/user_list/?users=foo&workspace=17"""
            @extend_schema(parameters=[
                OpenApiParameter("users", OpenApiTypes.STR),
                OpenApiParameter("workspace", OpenApiTypes.INT),
            ])
            def get(self, request, *args, **kwargs):
                return super().get(request, *args, **kwargs)

        return Fixed


class Fix2(OpenApiViewExtension):
    target_class = 'workspaces.views.BoardCreateWithoutWorkSpace'

    def view_replacement(self):
        class Fixed(self.target_class):
            """Создание доски без указания РП, будет создано дефолтное РП для этой доски"""
            pass

        return Fixed


class Fix3(OpenApiViewExtension):
    target_class = 'workspaces.views.TaskViewSet'

    def view_replacement(self):
        @extend_schema_view(list=extend_schema(description='Список всех задач колонки.'),
                            create=extend_schema(
                                description='Создать задачу\n\n'
                                            'responsible: Список ответсвенны пользователей. Передается массивом из id,'
                                            'например {"responsible": [1,2,3]}\n\n'
                                            'deadline: Срок выполнения задачи\n\n'
                                            'description: Описание\n\n'
                                            'priority: Приоритет, число от 0 до 3, где 0 - высочайший приоритет\n\n'
                                            'color_mark: Цвет метки\n\n'
                                            'name_mark: Название метки', ),
                            retrieve=extend_schema(description='Информация о конкретной задаче'),
                            update=extend_schema(
                                description='Обновить задачу.\n\n'
                                            'Для преремещения между колонок нужно передать column - id новой '
                                            'колонки и index - куда ее вставить.'
                            ),
                            partial_update=extend_schema(
                                description='Частично обновить задачу.\n\n'
                                            'Перемещение между колонками возможно только PUT запросом'
                            ),
                            destroy=extend_schema(description='Удалить задачу'),
                            )
        class Fixed(self.target_class):
            pass

        return Fixed


class Fix4(OpenApiViewExtension):
    target_class = 'workspaces.views.WorkSpaceViewSet'

    def view_replacement(self):
        @extend_schema_view(
            list=extend_schema(description='Список всех Рабочих пространств авторизованного пользователя'),
            create=extend_schema(description='Создать Рабочее пространство'),
            retrieve=extend_schema(description='Информация о конктретном рабочем пространстве'),
            update=extend_schema(description='Обновить все данные РП (на данный момент только имя)'),
            partial_update=extend_schema(description='Частично обновить данные РП (на данный момент только имя)'),
            destroy=extend_schema(description='Удалить РП'),
        )
        class Fixed(self.target_class):
            @extend_schema(responses={201: serializers.WorkSpaceSerializer(many=True)}, )
            def create(self, request, *args, **kwargs):
                return super().create(request, *args, **kwargs)

            @extend_schema(description='Пригласить пользователя по email.\n\n'
                                       'Пользователи добавляются по одному.'
                                       'Если пользователя не существует, он будет создан.',
                           responses={200: serializers.WorkSpaceSerializer}, )
            def invite_user(self, request, *args, **kwargs):
                return super().invite_user(request, *args, **kwargs)

            @extend_schema(
                description='Подтверждение приглашения в РП.\n\nПройдя по ссылке пользователь будет добавлен в РП. '
                            'Ссылка на приглашение: invite/workspace/{token}\n\n'
                            'Если ответ 200 - у пользователя нет пароля, отправить на '
                            '/auth/users/reset_password_invited/\n\nОтвет 204 - у пользователя есть пароль ',
                responses={204: None, 200: serializers.InviteUserSerializer, },
            )
            def confirm_invite(self, request, *args, **kwargs):
                return super().confirm_invite(request, *args, **kwargs)

            @extend_schema(
                description='Удаление пользователей из РП\n\nУдаление как из участников так и из приглашенных',
                responses={200: serializers.WorkSpaceSerializer}, )
            def kick_user(self, request, *args, **kwargs):
                return super().kick_user(request, *args, **kwargs)

            @extend_schema(description='Повторная отправка ссылки с приглашением пользователя.',
                           responses={204: None, }, )
            def resend_invite(self, request, *args, **kwargs):
                return super().resend_invite(request, *args, **kwargs)

        return Fixed


class Fix5(OpenApiViewExtension):
    target_class = 'workspaces.views.TestSSEMessage'

    def view_replacement(self):
        class Fixed(self.target_class):
            """
            Создать SSE - передает случайную строку.\n\n
            Слушать /events/\n\n
            channel: test\n\n
            event_type: test_message
            """
            pass

        return Fixed


class Fix6(OpenApiViewExtension):
    target_class = 'workspaces.views.TestSSEUser'

    def view_replacement(self):
        class Fixed(self.target_class):
            """
            Создать SSE - передает текущего юзера.\n\n
            Слушать /events/\n\n
            channel: test\n\n
            event_type: test_user
            """
            pass

        return Fixed


class Fix7(OpenApiViewExtension):
    target_class = 'workspaces.views.BoardViewSet'

    def view_replacement(self):
        @extend_schema_view(list=extend_schema(description='Список всех досок указанного РП.'),
                            create=extend_schema(description='Создать Доску'),
                            retrieve=extend_schema(description='Информация о конкретной доске'),
                            update=extend_schema(description='Обновить доску'),
                            partial_update=extend_schema(description='Частично обновить доску'),
                            destroy=extend_schema(description='Удалить доску'),
                            )
        class Fixed(self.target_class):
            pass

        return Fixed


class Fix8(OpenApiViewExtension):
    target_class = 'workspaces.views.ColumnViewSet'

    def view_replacement(self):
        @extend_schema_view(list=extend_schema(description='Список всех колонок доски.'),
                            create=extend_schema(description='Создать колонку на доске'),
                            retrieve=extend_schema(description='Информация о конкретной колонке'),
                            update=extend_schema(description='Обновить колонку (название и порядковый номер)'),
                            partial_update=extend_schema(
                                description='Частично обновить колонку (название/порядковый номер)'),
                            destroy=extend_schema(description='Удалить колонку'),
                            )
        class Fixed(self.target_class):
            pass

        return Fixed


class Fix9(OpenApiViewExtension):
    target_class = 'workspaces.views.StickerViewSet'

    def view_replacement(self):
        @extend_schema_view(list=extend_schema(description='Список стикеров задачи.'),
                            create=extend_schema(description='Создать стикер к задаче'),
                            retrieve=extend_schema(description='Представление одного стикера'),
                            update=extend_schema(description='Обновить стикер'),
                            partial_update=extend_schema(
                                description='Частично обновить стикер'),
                            destroy=extend_schema(description='Удалить стикер'),
                            )
        class Fixed(self.target_class):
            pass

        return Fixed