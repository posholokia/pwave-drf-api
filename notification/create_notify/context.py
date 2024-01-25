from datetime import datetime

from django.contrib.auth import get_user_model

from notification.create_notify.utils import generate_task_link, end_deadline_notify, create_notification

from workspaces.models import Task, WorkSpace, Column

User = get_user_model()


class NotifyContext:
    def __init__(self, request, obj, user, old=None):
        self.request = request
        self.obj = obj
        self.user = user
        self.old = old
        self.data = None
        assert False if type(obj) is Task and old is None else True, \
            'Не передано состояние таски перед выполнением запроса'

    def handler(self):
        self.get_empty_data()
        self.fill_common_data()
        context = self.get_context()
        create_notification(self.data, context)

    def get_context(self):
        data_keys = list(self.request['data'].keys())
        context = {}

        if type(self.obj) is Task:
            recipients = set(
                self.obj.responsible
                .exclude(pk=self.user['id'])
                .values_list('id', flat=True)
            )

        if self.request['method'] == 'DELETE':
            context.update({
                'delete_task': {
                    'col': self.obj.column.name,
                    'recipients': list(recipients),
                }
            })
            return context

        if 'responsible' in data_keys:
            new_users = recipients
            old_users = {self.old['responsible']}

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

    def get_empty_data(self):
        self.data = {
            'user': self.user['name'],
            'board': None,
            'workspace': None,
        }

    def fill_common_data(self):
        if type(self.obj) is Task:
            board = self.obj.column.board
            self.data['workspace'] = board.work_space_id
            self.data['board'] = board.id
            self.data['task'] = self.obj.name
            self.data['link'] = generate_task_link(
                board.work_space_id,
                board.id,
                self.obj.id
            )
        elif type(self.obj) is WorkSpace:
            self.data['workspace'] = self.obj.id
