from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_save, m2m_changed
from django.dispatch import receiver

from notification.logic.create_notification import notification_workspace_users
from workspaces.models import Board, Column, Task, Sticker, WorkSpace

User = get_user_model()


@receiver(post_save, sender=Board)
def create_board(sender, instance, created, **kwargs):
    if created:
        col = Column.objects.create(name='Надо сделать', board=instance, index=0)
        Column.objects.create(name='В работе', board=instance, index=1)
        Column.objects.create(name='Готово', board=instance, index=2)

        task = Task.objects.create(
            name='Моя первая задача',
            index=0,
            column=col,
            priority=2,
        )

        Sticker.objects.create(name='Стикер', color='#7033ff', task=task)


# @receiver(m2m_changed, sender=WorkSpace.invited.through)
# def notification_ws_users(sender, instance, pk_set, action, **kwargs):
#
#     if action == 'post_add':
#         notification_workspace_users(instance, pk_set, notify_type='added_in_ws')
#
#
# @receiver(m2m_changed, sender=WorkSpace.users.through)
# def notification_kick(sender, instance, pk_set, action, **kwargs):
#     if action == 'post_remove':
#         notification_workspace_users(instance, pk_set, notify_type='del_from_ws')
#
#
# @receiver(m2m_changed, sender=Task.responsible.through)
# def notification_kick(sender, instance, pk_set, action, **kwargs):
#     if action == 'post_add':
#         notification_workspace_users(instance, pk_set, notify_type='added_in_task')