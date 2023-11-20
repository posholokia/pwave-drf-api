import os

from celery import Celery
from celery.schedules import crontab
from celery import bootsteps
from celery.signals import worker_ready, worker_shutdown

from pathlib import Path

HEARTBEAT_FILE = Path("/tmp/worker_heartbeat")
READINESS_FILE = Path("/tmp/worker_ready")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pulsewave.settings')


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


app = Celery('pulsewave')
app.steps["worker"].add(LivenessProbe)

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'clear_tokens': {
        'task': 'taskmanager.tasks.clear_expired_token',
        'schedule': crontab(hour='1', minute='0'),
    },
}
