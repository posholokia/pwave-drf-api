from django.conf import settings


broker_url = (f'redis://{settings.REDIS_USER}:'
              f'{settings.REDIS_PASS}@'
              f'{settings.REDIS_HOST}:'
              f'6379/0')
result_backend = (f'redis://{settings.REDIS_USER}:'
                  f'{settings.REDIS_PASS}@'
                  f'{settings.REDIS_HOST}:'
                  f'{settings.REDIS_PORT}/0')
accept_content = ['application/json']
task_serializer = 'json'
result_serializer = 'json'
broker_connection_retry_on_startup = True
beat_scheduler = "django_celery_beat.schedulers:DatabaseScheduler"
enable_utc = True

