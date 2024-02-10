from datetime import datetime

from django.contrib.auth import get_user_model

from notification.create_notify.utils import generate_task_link, end_deadline_notify, create_notification

from workspaces.models import Task, WorkSpace, Column, Board

User = get_user_model()


class NotifyFactory:
    def __init__(self, request, obj, user, old=None):
        self.request = request
        self.obj = obj
        self.user = user
        self.old = old
        self.data = None
        # assert False if type(obj) is Task and old is None else True, \
        #     'Не передано состояние обьекта Task до выполнения request'

    def handler(self):
        print('\n\nNOTIFY\n\n')
        self._get_empty_data()
        self._fill_common_data()
        context = self.get_context()
        create_notification(self.data, context)

    def get_context(self):
        data_keys = list(self.request['data'].keys())
        context = {}

        if self.request['method'] == 'DELETE':  # сделать нормальную логику при удалении таски
            context.update({
                'delete_task': {
                    'col': Column.objects.get(pk=self.old['column']).name,
                    'recipients': list({*self.old['responsible']}.difference({self.user['id']})),
                }
            })
            return context

        if type(self.obj) is Task:
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

        if 'message' in data_keys:
            print(f'\n\n{list(recipients)=}')
            context.update({
                'add_comment': {
                    'recipients': list(recipients)
                },
            })

        return context

    def _get_empty_data(self):
        self.data = {
            'user': self.user['name'],
            'board': None,
            'workspace': None,
        }

    def _fill_common_data(self):
        if self.obj is None:  # сделать нормальную логику при удалении таски
            return self._fill_for_deleted_task()
        elif type(self.obj) is Task:
            board = self.obj.column.board
            self.data['workspace'] = board.work_space_id
            self.data['board'] = board.id
            self.data['task'] = self.obj.name
            self.data['link'] = generate_task_link(
                board.work_space_id,
                board.id,
                self.old['id']
            )
        elif type(self.obj) is WorkSpace:
            self.data['workspace'] = self.obj.id

    def _fill_for_deleted_task(self):
        board = Board.objects.get(column_board=self.old['column'])
        self.data['workspace'] = board.work_space_id
        self.data['board'] = board.id
        self.data['task'] = self.old['name']
        self.data['link'] = generate_task_link(
            board.work_space_id,
            board.id,
            self.old['id']
        )


class TaskNotification(NotifyFactory):
    pass


class WorkSpaceNotification(NotifyFactory):
    pass


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

