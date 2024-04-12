import json
import logging
import zoneinfo
import redis

from typing import Tuple

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.conf import settings

from django_celery_beat.models import PeriodicTask, CrontabSchedule

from channels.layers import get_channel_layer

from notification.models import Notification
from notification.serializers import NotificationListSerializer
from telebot.models import TeleBotID
from workspaces.models import Task
from workspaces.websocket.utils import group_send_data

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

User = get_user_model()


def end_deadline_notify(task: Task):
    """
    Создание отложенной задачи в celery-beat на
    создание уведомления об истечении дедлайна
    """
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


def get_current_task(pk: int) -> dict | None:
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


def get_user_data(user: User) -> dict:
    user_data = {
        'id': user.id,
        'name': user.representation_name(),
    }
    return user_data


def send_notification_to_redis(message: str, users: list[int]):
    """
    Функция отправляет в редис сообщение, которое публикует бот.
    message - строка.
    users - список из id телеграм чатов пользователей.
    """
    redis_client = redis.Redis(
        username=f'{settings.REDIS_USER}',
        password=f'{settings.REDIS_PASS}',
        host=f'{settings.REDIS_HOST}',
        port=f'{settings.REDIS_PORT}',
        db=3
    )
    data = {
        'message': message,
        'users': users,
    }
    redis_client.publish('notify', json.dumps(data))


def get_telegram_id(users: list[int]) -> list[int]:
    """
    Получение id телеграм чатов для
    рассылки уведомлений по id пользователей
    """
    chat_ids = list(TeleBotID.objects
                    .filter(user_id__in=users)
                    .values_list('telegram_id', flat=True)
                    )
    return chat_ids


def sending_to_channels(notification: Notification,
                        recipients: list[int]) -> None:
    """Рассылка уведомлений с сервера в другие каналы"""
    logger.info(f'Рассылка уведомлений по каналам')

    # в телеграм
    telegram_id_list = get_telegram_id(recipients)
    send_notification_to_redis(
        notification.text, telegram_id_list
    )

    # по вебсокету
    channel_layer = get_channel_layer()
    data = NotificationListSerializer(notification).data
    for user_id in recipients:
        group_send_data(channel_layer,
                        f'notification-{user_id}',
                        data
                        )


def get_pre_inintial_data(user: User,
                          task_id: int) -> Tuple[dict, dict]:
    user_data = get_user_data(user)
    task_data = get_current_task(task_id)
    return user_data, task_data
