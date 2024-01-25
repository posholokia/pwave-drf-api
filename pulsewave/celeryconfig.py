import os
from dotenv import load_dotenv

load_dotenv()


REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

broker_url = f'redis://{REDIS_HOST}:6379/0'
result_backend = f'redis://{REDIS_HOST}:6379/0'
accept_content = ['application/json']
task_serializer = 'json'
result_serializer = 'json'
broker_connection_retry_on_startup = True
beat_scheduler = "django_celery_beat.schedulers:DatabaseScheduler"
enable_utc = True
# redis_host = REDIS_HOST
# redis_port = '6379'
# redis_db = '0'
