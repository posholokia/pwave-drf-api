from celery import shared_task
from django_celery_beat.models import PeriodicTask

from .models import InvitedUsers


@shared_task
def delete_invitation_to_ws(invitation_id):
    invitation = InvitedUsers.objects.filter(id=invitation_id).first()

    if invitation:
        task = PeriodicTask.objects.get(name=f'delete_invitation-{invitation_id}')
        invitation.delete()
        task.delete()
