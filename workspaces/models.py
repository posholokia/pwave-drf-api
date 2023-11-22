from django.db import models
from pulsewave import settings
from django.utils.crypto import get_random_string


class WorkSpace(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='space_owner', on_delete=models.CASCADE)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='workspace_users')
    invited = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='workspace_invited')
    name = models.CharField('Рабочее пространство', max_length=50)
    created_at = models.DateTimeField('Время создания', auto_now_add=True)


class Board(models.Model):
    work_space = models.ForeignKey(WorkSpace, related_name='board', on_delete=models.CASCADE)
    name = models.CharField('Доска', max_length=50)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='board_members')


class InvitedUsers(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='invited', on_delete=models.CASCADE)
    token = models.CharField(max_length=24)
    workspace = models.ForeignKey(WorkSpace, related_name='invited_users', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

