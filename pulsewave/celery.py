import os

from celery import Celery

# Файл из документации к Celery. Менялось только название проекта.
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pulsewave.settings')  # Поменял имя проекта тут.

app = Celery('pulsewave')  # И тут.

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'every': {
        'task': 'taskmanager.tasks.clear_expired_token',
        'schedule': crontab(hour='1', minute='1'),
    },

}


