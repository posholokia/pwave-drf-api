import logging
from datetime import datetime
from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django_celery_beat.models import PeriodicTask

from notification.create_notify.mixin import TaskCommonDataMixin
from notification.create_notify.utils import end_deadline_notify, sending_to_channels
from notification.create_notify.notification_type import NOTIFICATION_TYPE as MESSAGE
from notification.models import Notification

from workspaces.models import Column, Board

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


User = get_user_model()


class NotifyFactory:
    def __init__(self,
                 request: Optional[dict] = None,
                 obj=None,
                 user: Optional[dict] = None
                 ):
        self.request = request
        self.obj = obj
        self.user = user
        self.data = None

    def handler(self):
        logger.info(f'Сработал хэндлер создания уведомлений')
        self.get_empty_data()
        self.fill_common_data()
        context = self.get_context()
        self.create_notification(self.data, context)

    def get_empty_data(self):
        self.data = {
            'user': self.user['name'],
            'board': None,
            'workspace': None,
        }

    @staticmethod
    def create_notification(data: dict[str],
                            context: dict[str:dict]) -> None:
        """
        Функция создания уведомлений.
        data: словарь, созержащий РП, доску и пользователя.
        context: контекст сообщения. Состоит из словарей, в котором:
            ключи: событие, по которому формируется уведомление,
            значения: содержит получателей и контекст для форматирования
            текста сообщения
        """
        logger.info(f'Создание уведомления...')
        for event, context in context.items():
            logger.info(f'Полученные данные для создания уведомления: {context=}, {data=}')
            text = MESSAGE[event].format(**context, **data)
            workspace = data['workspace']
            board = data['board']
            recipients = context['recipients']
            logger.info(f'Получатели уведомления: {recipients}')
            if recipients:
                notification = Notification.objects.create(
                    text=text,
                    workspace_id=workspace,
                    board_id=board,
                )
                logger.info(f'Уведомление создано: {notification}')
                notification.recipients.set(recipients)
                sending_to_channels(notification, recipients)

    @staticmethod
    def generate_task_link(workspace: int, board: int, task: int) -> str:
        """Формирование ссылки на задачу (Task)"""
        link = (f'{settings.DOMAIN}/'
                f'workspace/{workspace}/'
                f'board/{board}/'
                f'task/{task}')
        return link

    def fill_common_data(self):
        """
        Формирует общие данные для создания уведомлений,
        Например РП, доска, и др, в зависимости от текста сообщений.
        Метод должен обновить словарь self.data
        Переопредели, в зависимости от того, какие данные
        передаются при инициализации класса
        """
        pass

    def get_context(self):
        """
        Формирует контекст для создания уведомления.
        Контекст должен быть словарем, в котором:
            ключи - события для отправки уведомлений (см. NOTIFICATION_TYPE),
            значения - словарь содержащий ключи:
                recipients: список из id получателей уведомления (обязателен)
                и другие ключи, которые нужно вставить в текст уведомления.
        Возвращает контекст.
        """
        pass


class TaskNotification(TaskCommonDataMixin, NotifyFactory):
    def __init__(self, event_data, obj, user, old: dict):
        super().__init__(obj=obj, user=user)
        self.old = old
        self.event_data = event_data

    def get_context(self):
        data_keys = list(self.event_data.keys())
        context = {}
        recipients = set(
            self.obj.responsible
            .exclude(pk=self.user['id'])
            .values_list('id', flat=True)
        )

        if 'responsible' in data_keys:
            new_users = recipients
            old_users = {*self.old['responsible']}

            added = new_users.difference(old_users, {self.user['id']})
            deleted = old_users.difference(new_users, {self.user['id']})

            if added:
                context.update({
                    'added_in_task': {
                        'recipients': list(added)
                    },
                })
            if deleted:
                context.update({
                    'delete_from_task': {
                        'recipients': list(deleted)
                    }
                })

        if 'column' in data_keys:
            old_col = Column.objects.get(pk=self.old['column'])
            new_col = self.obj.column

            if old_col != new_col:
                context.update({
                    'move_task': {
                        'old_col': old_col.name,
                        'new_col': new_col.name,
                        'recipients': list(recipients),
                    }
                })

        if 'deadline' in data_keys:
            old_deadline = self.old['deadline']
            new_deadline = self.obj.deadline

            if new_deadline:
                # запуск отложенной задачи об окончании дедлайна
                end_deadline_notify(self.obj)

                if old_deadline is None:
                    context.update({
                        'deadline_task': {
                            'date': datetime.strftime(new_deadline, '%Y-%m-%dT%H:%M%z'),
                            'recipients': list(recipients),
                        }
                    })
                elif old_deadline != new_deadline:
                    context.update({
                        'change_deadline': {
                            'date': datetime.strftime(new_deadline, '%Y-%m-%dT%H:%M%z'),
                            'recipients': list(recipients),
                        }
                    })

        if 'name' in data_keys:
            if self.obj.name != self.old['name']:
                context.update({
                    'change_name': {
                        'old_name': self.old['name'],
                        'recipients': list(recipients),
                    },
                })

        if 'priority' in data_keys:
            if self.obj.priority is None:
                priority = 'Отсутствует'
            else:
                priority = self.obj.get_priority_display()

            if self.obj.priority != self.old['priority']:
                context.update({
                    'change_priority': {
                        'priority': priority,
                        'recipients': list(recipients),
                    },
                })
        logger.info(f'Собран контекст для уведомления, {self.__class__} {context=}')
        return context


class WorkSpaceNotification(NotifyFactory):
    def fill_common_data(self):
        self.data['workspace'] = self.obj.id

    def get_context(self):
        data_keys = list(self.request['data'].keys())
        context = {}

        if 'email' in data_keys:
            context.update({
                'added_in_ws': {
                    'ws': self.obj.name,
                    'recipients': [
                        User.objects
                        .values_list('id', flat=True)
                        .get(email=self.request['data']['email'])
                    ],
                }
            })

        if 'user_id' in data_keys:
            context.update({
                'del_from_ws': {
                    'ws': self.obj.name,
                    'recipients': [self.request['data']['user_id']],
                }
            })
        logger.info(f'Собран контекст для уведомления, {self.__class__} {context=}')
        return context


class DeleteTaskNotification(TaskNotification):
    def fill_common_data(self):
        board = Board.objects.get(column_board=self.old['column'])
        self.data['workspace'] = board.workspace_id
        self.data['board'] = board.id
        self.data['task'] = self.old['name']
        self.data['link'] = self.generate_task_link(
            board.workspace_id,
            board.id,
            self.old['id']
        )

    def get_context(self):
        column = Column.objects.get(pk=self.old['column']).name
        recipients = {*self.old['responsible']}.difference({self.user['id']})

        context = {
            'delete_task': {
                'col': column,
                'recipients': list(recipients),
            }
        }
        logger.info(f'Собран контекст для уведомления, {self.__class__} {context=}')
        return context


class CommentNotification(TaskCommonDataMixin, NotifyFactory):
    def get_context(self):
        data_keys = list(self.request['data'].keys())
        context = {}

        recipients = set(
            self.obj.responsible
            .exclude(pk=self.user['id'])
            .values_list('id', flat=True)
        )

        if 'message' in data_keys:
            context.update({
                'add_comment': {
                    'recipients': list(recipients)
                },
            })
        logger.info(f'Собран контекст для уведомления, {self.__class__} {context=}')
        return context


class DeadlineNotification(TaskCommonDataMixin, NotifyFactory):
    def handler(self):
        super().handler()
        PeriodicTask.objects.get(
            name=f'end_deadline_{self.obj.id}'
        ).delete()

    def get_empty_data(self):
        self.data = {
            'board': None,
            'workspace': None,
        }

    def get_context(self):
        recipients = set(
            self.obj.responsible
            .values_list('id', flat=True)
        )
        context = {
            'end_deadline': {
                'recipients': list(recipients)
            },
        }
        logger.info(f'Собран контекст для уведомления, {self.__class__} {context=}')
        return context
