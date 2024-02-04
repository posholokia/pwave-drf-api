from django.db import models

from pulsewave import settings


class TeleBotID(models.Model):
    user = models.OneToOneField(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    telegram_id = models.PositiveIntegerField()
    name = models.CharField(max_length=32)
