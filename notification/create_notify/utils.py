import json
import zoneinfo

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from django_celery_beat.models import PeriodicTask, CrontabSchedule

from notification.models import Notification
from notification.create_notify.notification_type import NOTIFICATION_TYPE as MESSAGE
from sse.senders import sse_send_notifications
from workspaces.models import Task

User = get_user_model()


def generate_task_link(workspace: int, board: int, task: int) -> str:
    """Формирование ссылки на задачу (Task)"""
    link = (f'{settings.DOMAIN}/'
            f'workspace/{workspace}/'
            f'board/{board}/'
            f'task/{task}')
    return link


def create_notification(data: dict[str:dict], context: dict[str:dict]) -> None:
    """
    Функция создания уведомлений. Принимает словарь, где ключи - это события,
    по которым создаются уведомления (список событий и сообщений для этого
    события в NOTIFICATION_TYPE), а значения ключей - контекст для текста сообщения.
    Обязательно должен быть ключ "common", в котором содержится РП и Доска,
    с которым связано уведомление (а также можно разместить контекст текста уведомления)
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
            sse_send_notifications(notification, recipients)


def end_deadline_notify(task: Task):
    if task.deadline is None:
        p = PeriodicTask.objects.filter(name=f'end_deadline_{task.id}').first()
        if p:
            p.delete()

    month = str(task.deadline.month)
    day = str(task.deadline.day)
    hour = str(task.deadline.hour)
    minute = str(task.deadline.minute)

    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute=minute,
        hour=hour,
        day_of_week='*',
        day_of_month=day,
        month_of_year=month,
        timezone=zoneinfo.ZoneInfo('UTC')
    )
    try:
        PeriodicTask.objects.create(
            crontab=schedule,
            name=f'end_deadline_{task.id}',
            task='notification.create_notify.tasks.end_deadline',
            args=json.dumps([task.id])
        )
    except ValidationError:
        p_task = PeriodicTask.objects.get(name=f'end_deadline_{task.id}')
        p_task.crontab = schedule
        p_task.save()


def get_current_task(pk):
    try:
        task = Task.objects.get(pk=pk)
        data = {
            'id': pk,
            'name': task.name,
            'column': task.column_id,
            'responsible': list(task.responsible.values_list('id', flat=True)),
            'deadline': task.deadline,
            'priority': task.priority,
        }
        return data
    except Task.DoesNotExist:
        return



def get_user_data(user):
    user_data = {
        'id': user.id,
        'name': user.representation_name(),
    }
    return user_data
