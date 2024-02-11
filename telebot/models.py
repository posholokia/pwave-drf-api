from django.db import models

from pulsewave import settings


class TeleBotID(models.Model):
    user = models.OneToOneField(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    telegram_id = models.PositiveBigIntegerField()
    name = models.CharField(max_length=32)

    def __repr__(self):
        return (f'{self.__class__} '
                f'User: {self.user}, '
                f'Telegram: {self.telegram_id}')
