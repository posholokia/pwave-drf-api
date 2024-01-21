import locale

from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model

from workspaces.models import Task, Column, WorkSpace

locale.setlocale(locale.LC_ALL, 'ru_RU.utf8')

User = get_user_model()


def get_task_data(*args, **kwargs):
    request = args[1]
    obj_id = kwargs.get('pk')
    task = Task.objects.get(pk=obj_id)

    board = task.column.board
    link = generate_task_link(board, task)

    data = {
        'common': {
            'user': request.user.representation_name(),
            'link': link,
            'task': task.name,
            'workspace': board.work_space_id,
            'board': board.id,
        },
    }

    notify_context = get_task_notify_context(request, task)
    data.update(**notify_context)
    return data


def generate_task_link(board, task):
    link = (f'{settings.DOMAIN}/'
            f'workspace/{board.work_space_id}/'
            f'board/{board.id}/'
            f'task/{task.id}')
    return link


def get_task_notify_context(request, task):
    data = request.data
    user_id = request.user.id
    data_keys = list(data.keys())
    context = {}

    recipients = set(task.responsible.exclude(pk=user_id).values_list('id', flat=True))

    if request.method == 'DELETE':
        context.update({
            'delete_task': {
                'col': task.column.name,
                'recipients': list(recipients),
            }
        })
        return context

    if 'responsible' in data_keys:
        new_users = set(data['responsible'])
        old_users, recipients = recipients, new_users

        added = new_users.difference(old_users, {user_id})
        deleted = old_users.difference(new_users, {user_id})

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
        old_col = task.column
        new_col = Column.objects.get(pk=data['column'])

        if old_col is not None and old_col != new_col:
            context.update({
                'move_task': {
                    'old_col': old_col.name,
                    'new_col': new_col.name,
                    'recipients': list(recipients),
                }
            })

    if 'deadline' in data_keys and data['deadline']:
        old_deadline = task.deadline
        deadline_str = data['deadline']
        new_deadline = (
            datetime
            .strptime(deadline_str, '%Y-%m-%d')
            .date()
        )

        if old_deadline is None:
            context.update({
                'deadline_task': {
                    'date': datetime.strftime(new_deadline, '%d %B %Y'),
                    'recipients': list(recipients),
                }
            })
        elif old_deadline != new_deadline:
            context.update({
                'change_deadline': {
                    'date': datetime.strftime(new_deadline, '%d %B %Y'),
                    'recipients': list(recipients),
                }
            })

    return context


def get_ws_data(*args, **kwargs):
    request = args[1]
    obj_id = kwargs.get('pk')

    workspace = WorkSpace.objects.get(pk=obj_id)

    data = {
        'common': {
            'workspace': workspace.id,
            'board': None,
        }
    }
    notify_context = get_ws_notify_context(request, workspace)
    data.update(**notify_context)
    return data


def get_ws_notify_context(request, workspace):
    data = request.data
    data_keys = list(data.keys())
    context = {}

    if 'email' in data_keys:
        context.update({
            'added_in_ws': {
                'ws': workspace.name,
                'recipients': [User.objects.values_list('id', flat=True).get(email=data['email'])],
            }
        })

    if 'user_id' in data_keys:
        context.update({
            'del_from_ws': {
                'ws': workspace.name,
                'recipients': [data['user_id']],
            }
        })
    return context
