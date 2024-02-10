from datetime import datetime

from django.contrib.auth import get_user_model

from notification.create_notify.utils import generate_task_link, end_deadline_notify, sending_to_channels
from notification.create_notify.notification_type import NOTIFICATION_TYPE as MESSAGE
from notification.models import Notification

from workspaces.models import Column, Board

User = get_user_model()


class NotifyFactory:
    def __init__(self, request, obj, user):
        self.request = request
        self.obj = obj
        self.user = user
        self.data = None

    def handler(self):
        self._get_empty_data()
        self._fill_common_data()
        context = self.get_context()
        self.create_notification(self.data, context)

    def _get_empty_data(self):
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

        for event, context in context.items():
            text = MESSAGE[event].format(**context, **data)
            workspace = data['workspace']
            board = data['board']
            recipients = context['recipients']

            if recipients:
                notification = Notification.objects.create(
                    text=text,
                    workspace_id=workspace,
                    board_id=board,
                )
                notification.recipients.set(recipients)
                sending_to_channels(notification, recipients)

    def _fill_common_data(self):
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


class TaskNotification(NotifyFactory):
    def __init__(self, request, obj, user, old):
        super().__init__(request, obj, user)
        self.old = old

    def _fill_common_data(self):
        board = self.obj.column.board
        self.data['workspace'] = board.work_space_id
        self.data['board'] = board.id
        self.data['task'] = self.obj.name
        self.data['link'] = generate_task_link(
            board.work_space_id,
            board.id,
            self.obj.id
        )

    def get_context(self):
        data_keys = list(self.request['data'].keys())
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

        return context


class WorkSpaceNotification(NotifyFactory):
    def _fill_common_data(self):
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

        return context


class DeleteTaskNotification(TaskNotification):
    def _fill_common_data(self):
        board = Board.objects.get(column_board=self.old['column'])
        self.data['workspace'] = board.work_space_id
        self.data['board'] = board.id
        self.data['task'] = self.old['name']
        self.data['link'] = generate_task_link(
            board.work_space_id,
            board.id,
            self.old['id']
        )

    def get_context(self):
        context = {}
        context.update({
            'delete_task': {
                'col': Column.objects.get(pk=self.old['column']).name,
                'recipients': list({*self.old['responsible']}.difference({self.user['id']})),
            }
        })

        return context


class CommentNotification(NotifyFactory):
    def _fill_common_data(self):
        board = self.obj.column.board
        self.data['workspace'] = board.work_space_id
        self.data['board'] = board.id
        self.data['task'] = self.obj.name
        self.data['link'] = generate_task_link(
            board.work_space_id,
            board.id,
            self.obj.id
        )

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

        return context
