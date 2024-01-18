from django.db import models
from django.conf import settings


class Notification(models.Model):
    text = models.CharField('Текст сообщения', max_length=256)
    created_at = models.DateTimeField('Время создания', auto_now_add=True)
    read = models.BooleanField('Прочитано', default=False)
    recipients = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='notification')
