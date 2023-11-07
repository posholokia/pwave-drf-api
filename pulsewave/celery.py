import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pulsewave.settings')

app = Celery('pulsewave')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'clear_tokens': {
        'task': 'taskmanager.tasks.clear_expired_token',
        'schedule': crontab(hour='1', minute='0'),
    },
}
