from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .tasks import delete_invitation_to_ws
from .models import InvitedUsers


@receiver(post_save, sender=InvitedUsers)
def delete_invitation(sender, instance, created, **kwargs):
    if created:
        delete_invitation_to_ws.apply_async((instance.id,), countdown=24*60*60)
