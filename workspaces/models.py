from django.db import models
from pulsewave import settings


class WorkSpace(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='owned_workspaces', on_delete=models.CASCADE)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='joined_workspaces')
    invited = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='invited_to_workspaces')
    name = models.CharField('Рабочее пространство', max_length=50)
    created_at = models.DateTimeField('Время создания', auto_now_add=True)


class Board(models.Model):
    work_space = models.ForeignKey(WorkSpace, related_name='boards', on_delete=models.CASCADE)
    name = models.CharField('Доска', max_length=50)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='joined_boards')


class InvitedUsers(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='invitations', on_delete=models.CASCADE)
    token = models.CharField(max_length=32)
    workspace = models.ForeignKey(WorkSpace, related_name='workspace_invitations', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

