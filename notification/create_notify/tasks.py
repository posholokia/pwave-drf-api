from django_celery_beat.models import PeriodicTask

from django.contrib.auth import get_user_model

from celery import shared_task

from notification.create_notify.context import NotifyContext
from notification.create_notify.utils import (generate_task_link,
                                              create_notification)
from workspaces.models import Task, WorkSpace

User = get_user_model()


@shared_task
def end_deadline(pk):
    task = Task.objects.get(pk=pk)
    board = task.column.board
    workspace = board.work_space_id
    recipients = task.responsible.values_list('id', flat=True)
    link = generate_task_link(workspace, board, task.id)

    data = {
        'link': link,
        'task': task,
        'workspace': workspace,
        'board': board.id,
    }
    context = {
        'end_deadline': {
            'recipients': list(recipients)
        }
    }
    create_notification(data, context)
    PeriodicTask.objects.get(name=f'end_deadline_{pk}').delete()


@shared_task
def run_task_notification(old, user, request):
    if request['method'] != 'DELETE':  # TODO сделать нормальную логику при удалении таски
        task = Task.objects.get(pk=old['id'])
    else:
        task = None
    NotifyContext(request, task, user, old).handler()


@shared_task
def run_ws_notification(user, request, pk):
    ws = WorkSpace.objects.get(pk=pk)
    NotifyContext(request, ws, user).handler()
