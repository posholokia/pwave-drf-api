from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from workspaces.models import Board, Column, Task, Sticker

User = get_user_model()


@receiver(post_save, sender=Board)
def create_board(sender, instance, **kwargs):
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


