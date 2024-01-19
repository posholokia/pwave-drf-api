from datetime import datetime

from workspaces.models import WorkSpace, Task
from .notification_type import NOTIFICATION_TYPE as MESSAGE
from notification.models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()


def create_notification(context):
    pass


def notification_workspace_users(workspace: WorkSpace,
                                 user_pk: set,
                                 notify_type: str) -> None:
    context = {
        'workspace': workspace.name
    }
    text = MESSAGE[notify_type].format(**context)
    recipients = User.objects.get(pk=user_pk.pop())
    notify = Notification.objects.create(
        text=text,
        workspace=workspace,
    )
    notify.recipients.add(recipients)


def task_change_notify(func):
    def wrapper(*args, **kwargs):
        context = get_task_context(*args, **kwargs)
        res = func(*args, **kwargs)
        status = res.status_code
        if status == 200 or status == 201:
            create_notification(context)
        return res
    return wrapper


def get_task_context(*args, **kwargs):
    request = args[1]
    obj_id = kwargs.get('pk', None)
    obj = Task.objects.get(pk=obj_id)

    context = {
        'common': {
            'user': request.user,
            'link': request.path,
            'task': obj,
            'workspace': obj.column.board.work_space,
            'board': obj.column.board,
        },
    }
    notify_context = get_task_notify_context(request.data, obj)
    context.update(**notify_context)
    return context


def get_task_notify_context(data, task):
    data_keys = list(data.keys())
    context = {}

    if 'responsible' in data_keys:
        new_users = set(data['responsible'])
        old_users = set(task.responsible.all().values_list('id', flat=True))
        added = new_users.difference(old_users)
        deleted = old_users.difference(new_users)

        if added:
            print('\nadded_in_task\n')
            context.update({'added_in_task': added})
        if deleted:
            print('\ndelete_from_task\n')
            context.update({'delete_from_task': deleted})

    if 'column' in data_keys:
        old_col = task.column_id
        new_col = data['column']

        if old_col != new_col:
            print('\nmove_task\n')
            context.update({'move_task': (old_col, new_col)})

    if 'deadline' in data_keys and data['deadline']:
        old_deadline = task.deadline
        deadline_str = data['deadline']
        new_deadline = (datetime
                        .strptime(deadline_str, '%Y-%m-%d')
                        .date())

        if old_deadline is None:
            print('\ndeadline_task\n')
            context.update({'deadline_task': new_deadline})
        elif old_deadline != new_deadline:
            print('\nchange_deadline\n')
            context.update({'change_deadline': new_deadline})

    return context
