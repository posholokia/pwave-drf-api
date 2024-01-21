from notification.create_notify.notification_type import NOTIFICATION_TYPE as MESSAGE
from notification.models import Notification
from django.contrib.auth import get_user_model
from celery import shared_task

User = get_user_model()


@shared_task
def create_notification(data: dict[str:dict]) -> None:
    """
    Функция создания уведомлений. Принимает словарь, где ключи - это события,
    по которым создаются уведомления (список событий и сообщений для этого
    события в NOTIFICATION_TYPE), а значения ключей - контекст для текста сообщения.
    Обязательно должен быть ключ "common", в котором содержится РП и Доска,
    с которым связано уведомление (а также можно разместить контекст текста уведомления)
    """
    assert 'common' in data.keys(), ('В data отсутсвует ключ "common" c '
                                     'рабочим пространством и/или доской')
    data = data.copy()
    common = data.pop('common')

    for event, context in data.items():
        text = MESSAGE[event].format(**context, **common)
        workspace = common['workspace']
        board = common['board']
        recipients = context['recipients']

        if recipients:
            notification = Notification.objects.create(
                text=text,
                workspace_id=workspace,
                board_id=board,
            )
            notification.recipients.set(recipients)
