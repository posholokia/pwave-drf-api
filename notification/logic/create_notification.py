from workspaces.models import WorkSpace
from .notification_type import NOTIFICATION_TYPE as MESSAGE
from notification.models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()


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
