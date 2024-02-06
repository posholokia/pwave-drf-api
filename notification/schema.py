"""
Этот файл содержит дополнения и исправления схемы генерации OpenAPI
документации библиотеки drf-spectacular.
"""

from drf_spectacular.extensions import OpenApiViewExtension
from drf_spectacular.utils import extend_schema


class Fix1(OpenApiViewExtension):
    target_class = 'notification.views.NotificationList'

    def view_replacement(self):
        class Fixed(self.target_class):
            """
            Список уведомлений текущего пользователя.\n\n
            Получение через SSE:\n\n
            Канал: "/events/user/<user_id>/"\n\n
            Событие: "notification"\n\n
            Уведомления через SSE приходят по одному
            """

            @extend_schema(
                description='Отметить прочтение всех уведомлений',
                request=None,
            )
            def read_all(self, request, *args, **kwargs):
                return super().read_all(request, *args, **kwargs)

        return Fixed


class Fix2(OpenApiViewExtension):
    target_class = 'notification.views.NotificationUpdate'

    def view_replacement(self):
        class Fixed(self.target_class):
            """Отметить прочение одного уведомления"""

        return Fixed


# class Fix3(OpenApiViewExtension):
#     target_class = 'notification.views.NotificationList'
#
#     def view_replacement(self):
#         class Fixed(self.target_class):
#             """
#             Получение одной задачи.\n\n
#             Получение через SSE:\n\n
#             Канал: "/events/task/<task_id>/"\n\n
#             Событие: task
#             """
#         return Fixed
