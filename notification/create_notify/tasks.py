from notification.create_notify.notification_type import NOTIFICATION_TYPE as MESSAGE
from notification.models import Notification
from django.contrib.auth import get_user_model
from celery import shared_task

User = get_user_model()


@shared_task
def create_notification(data: dict):
    # print(f'\nTASK\n')
    data = data.copy()
    common = data.pop('common')
    # print(f'\n{data=}\n')
    # print(f'\n{common=}\n')

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
