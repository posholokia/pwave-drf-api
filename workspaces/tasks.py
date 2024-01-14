from celery import shared_task
from .models import InvitedUsers


@shared_task
def delete_invitation_to_ws(invitation_id):
    invitation = InvitedUsers.objects.filter(id=invitation_id).first()
    if invitation:
        invitation.delete()
