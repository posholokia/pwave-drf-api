from django_eventstream import send_event

from notification.serializers import NotificationListSerializer


def sse_send_notifications(obj, pks):
    data = NotificationListSerializer(obj).data
    for pk in pks:
        send_event(
            f'user-{pk}',
            'notification',
            data
        )
