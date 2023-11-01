from celery.schedules import crontab
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.utils import aware_utcnow
from pulsewave.celery import app


def _clear_expired_token():
    OutstandingToken.objects.filter(expires_at__lte=aware_utcnow()).delete()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Запуск очистки просроченных токенов
    sender.add_periodic_task(
        crontab(hour=17, minute=40,),
        _clear_expired_token(),
    )
