import os

from celery import Celery

# Файл из документации к Celery. Менялось только название проекта.

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pulsewave.settings')  # Поменял имя проекта тут.

app = Celery('pulsewave')  # И тут.

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
