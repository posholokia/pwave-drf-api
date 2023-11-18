from django.db import models
from pulsewave import settings


class WorkSpace(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='space_owner', on_delete=models.CASCADE)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='workspace_users')
    invited = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='workspace_invited', null=True)
    name = models.CharField('Рабочее пространство', max_length=30)
    created_at = models.DateTimeField('Время создания', auto_now_add=True)


class Board(models.Model):
    work_space = models.ForeignKey(WorkSpace, related_name='board', on_delete=models.CASCADE)
    name = models.CharField('Доска', max_length=30)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='board_members')
