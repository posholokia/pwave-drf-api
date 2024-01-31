"""
Этот файл содержит дополнения и исправления схемы генерации OpenAPI
документации библиотеки drf-spectacular.
"""

from drf_spectacular.extensions import OpenApiViewExtension


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
            pass

        return Fixed


class Fix2(OpenApiViewExtension):
    target_class = 'notification.views.NotificationUpdate'

    def view_replacement(self):
        class Fixed(self.target_class):
            """Отметить прочение уведомления"""
            pass

        return Fixed
