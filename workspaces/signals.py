import json
import zoneinfo
import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from workspaces.models import Board, Column, Task, Sticker, InvitedUsers

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


@receiver(post_save, sender=InvitedUsers)
def delete_invitation(sender, instance, created, **kwargs):
    if created:
        """
        Запускает задачу по удалению связанного приглашения
        """
        time_now = datetime.datetime.now()
        token_timeout = settings.WORKSAPCES.get('INVITE_TOKEN_TIMEOUT')

        if token_timeout:
            delta = token_timeout
        else:
            delta = 3600

        run_time = time_now + datetime.timedelta(seconds=delta)

        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=run_time.minute,
            hour=run_time.hour,
            day_of_week='*',
            day_of_month=run_time.day,
            month_of_year=run_time.month,
            timezone=zoneinfo.ZoneInfo('UTC')
        )

        PeriodicTask.objects.create(
            crontab=schedule,
            name=f'delete_invitation-{instance.id}',
            task='workspaces.tasks.delete_invitation_to_ws',
            args=json.dumps([instance.id])
        )
