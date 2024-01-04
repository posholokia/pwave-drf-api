from typing import Optional

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from workspaces.models import WorkSpace, Board
from .tasks import delete_inactive_user

User = get_user_model()


@receiver(post_save, sender=User)
def delete_user_task(sender, instance, **kwargs):
    delete_inactive_user.apply_async((instance.id,), countdown=24*60*60)


# @receiver(pre_save, sender=User)
# def create_default_workspace(sender, instance, **kwargs):
#     active = None
#     if instance.pk is not None:
#         try:
#             old_user = sender.objects.get(pk=instance.pk)
#             active = old_user.is_active
#         except:
#             pass
#
#     if active is False and instance.is_active is True:
#         workspace = WorkSpace.objects.create(owner=instance, name='Рабочее пространство 1')
#         workspace.users.add(instance)
