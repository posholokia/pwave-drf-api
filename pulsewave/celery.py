import os

from celery import Celery
from celery.schedules import crontab
from celery import bootsteps
from celery.signals import worker_ready, worker_shutdown, after_task_publish

from pathlib import Path


HEARTBEAT_FILE = Path("/tmp/celery_heartbeat")
READINESS_FILE = Path("/tmp/celery_ready")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pulsewave.settings')


# пробы готовности для celery-worker
class LivenessProbe(bootsteps.StartStopStep):
    requires = {'celery.worker.components:Timer'}

    def __init__(self, worker, **kwargs):
        print("LivenessProbe instance created!")
        self.requests = []
        self.tref = None

    def start(self, worker):
        self.tref = worker.timer.call_repeatedly(
            1.0, self.update_heartbeat_file, (worker,), priority=10,
        )

    def stop(self, worker):
        HEARTBEAT_FILE.unlink(missing_ok=True)

    def update_heartbeat_file(self, worker):
        HEARTBEAT_FILE.touch()


@worker_ready.connect
def worker_ready(**_):
    READINESS_FILE.touch()


@worker_shutdown.connect
def worker_shutdown(**_):
    READINESS_FILE.unlink(missing_ok=True)


# celery настройки
app = Celery('pulsewave')
app.steps["worker"].add(LivenessProbe)

app.config_from_object('pulsewave.celeryconfig')

app.autodiscover_tasks()


# пробы работоспособности celery-beat
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(60.0, celery_heartbeat.s(), name='celery_heartbeat')


@app.task
def celery_heartbeat():
    pass


@after_task_publish.connect(sender='pulsewave.celery.celery_heartbeat')
def task_published(**_):
    HEARTBEAT_FILE.touch()


# запуск периодических задач celery
app.conf.beat_schedule = {
    'clear_tokens': {
        'task': 'accounts.tasks.clear_expired_token',
        'schedule': crontab(hour='1', minute='0'),
    },
}
