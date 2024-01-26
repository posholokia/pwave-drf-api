from django.db import models
from django.conf import settings

from pulsewave.validators import validate_sticker_color


class WorkSpace(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='owned_workspaces', on_delete=models.CASCADE)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='joined_workspaces')
    invited = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='invited_to_workspaces')
    name = models.CharField('Рабочее пространство', max_length=50)
    created_at = models.DateTimeField('Время создания', auto_now_add=True)

    def __repr__(self):
        return f'{self.name}'


class Board(models.Model):
    work_space = models.ForeignKey(WorkSpace, related_name='board', on_delete=models.CASCADE)
    name = models.CharField('Доска', max_length=50)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='joined_boards')

    def __repr__(self):
        return f'{self.name}'


class InvitedUsers(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='invitations', on_delete=models.CASCADE)
    token = models.CharField(max_length=32)
    workspace = models.ForeignKey(WorkSpace, related_name='workspace_invitations', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class Column(models.Model):
    name = models.CharField('Колонка', max_length=50)
    board = models.ForeignKey(Board, related_name='column_board', on_delete=models.CASCADE)
    index = models.PositiveIntegerField('Порядковый номер')

    def __repr__(self):
        return f'{self.name}'


class Task(models.Model):
    PRIORITY = (
        (0, 'Срочный'),
        (1, 'Высокий'),
        (2, 'Нормальный'),
        (3, 'Низкий'),
    )
    name = models.CharField('Название задачи', max_length=50)
    index = models.PositiveIntegerField('Порядковый номер')
    column = models.ForeignKey(Column, related_name='task', on_delete=models.CASCADE)
    responsible = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='responsible_for_task')
    deadline = models.DateTimeField('Срок выполнения', null=True)
    description = models.CharField('Описание', max_length=2048, blank=True)
    file = models.FileField(upload_to='task_attach/', null=True)
    priority = models.IntegerField('Флаг приоритета', choices=PRIORITY, null=True)
    created_at = models.DateTimeField('Время создания задачи', auto_now_add=True)


class Sticker(models.Model):
    name = models.CharField('Название стикера', max_length=32)
    color = models.CharField('Цвет', max_length=7, validators=[validate_sticker_color, ])
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='sticker')


class Comment(models.Model):
    # related_name - это имя объекта при обратном обращении к нему.
    # Например, получить задачу из комментария - Comment.task - прямое обращение по названиям полей модели.
    # Но если из задачи нужно получить комментарии, используется related_name:
    # Task.task - не очевидно что это комментарии к задаче, как и User.author - не понятно, что это список комментариев.
    # Давай названия related_name, как если бы это поле не в этой модели, а в связанной.
    # Например, Task.comments или User.task_comments гораздо понятнее, что это комментарии
    # задачи и пользователя соответственно, чем Task.task и User.author.
    # А message переименовал чтобы не было конфликта имен
    task = models.ForeignKey(Task, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='task_comments', on_delete=models.CASCADE)
    message = models.CharField('Комментарий', max_length=2048)
    created_data = models.DateTimeField('Время создания комментария', auto_now_add=True)
