from django.db import models

from pulsewave import settings


class TeleBotID(models.Model):
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    telegram_id = models.PositiveIntegerField()
