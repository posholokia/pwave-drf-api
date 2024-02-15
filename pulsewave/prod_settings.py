import os
import sentry_sdk
import logging

from dotenv import load_dotenv

from sentry_sdk.integrations.logging import LoggingIntegration


load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')

DEBUG = False
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    },
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

DEFAULT_FROM_EMAIL = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST = 'smtp.yandex.ru'
EMAIL_PORT = 465
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_USE_SSL = True

AWS_ACCESS_KEY_ID = os.getenv('AWS_KEY_IDENTIFICATOR')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_KEY')
AWS_STORAGE_BUCKET_NAME = 'pulsewave'
AWS_S3_REGION_NAME = 'ru-central1'
AWS_S3_ENDPOINT_URL = 'https://storage.yandexcloud.net/'

STORAGES = {
    "default": {
        'BACKEND': 'storages.backends.s3.S3Storage',
    },
    'staticfiles': {
         'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
    }
}
AWS_S3_FILE_OVERWRITE = False

ADMINS = (
    ('admin', 'ilya.posholokk@gmail.com'),
)
SERVER_EMAIL = os.getenv('EMAIL_HOST_USER')

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'console': {
#             'format': '%(name)-12s %(levelname)-8s %(message)s'
#         },
#         'mail_admins': {
#             'format': '%(name)-12s %(levelname)-8s %(message)s'
#         },
#     },
#     'handlers': {
#         'console': {
#             'class': 'logging.StreamHandler',
#             'formatter': 'console'
#         },
#         'mail_admins': {
#             'level': 'ERROR',
#             'class': 'django.utils.log.AdminEmailHandler',
#             'include_html': True,
#         },
#     },
#     'loggers': {
#         '': {
#             'level': 'ERROR',
#             'handlers': ['console', 'mail_admins'],
#             'propagate': True
#         },
#         'django.request': {
#             'level': 'DEBUG',
#             'handlers': ['console', ]
#         }
#     }
# }


# ссылка на фронт, для формирования ссылок
DOMAIN = 'https://front.pwave.pnpl.tech'

# для доступа к админке
CSRF_TRUSTED_ORIGINS = ["https://api.pwave.pnpl.tech"]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# SSE
EVENTSTREAM_STORAGE_CLASS = 'sse.storage.RedisStorage'
EVENTSTREAM_ALLOW_ORIGIN = 'https://front.pwave.pnpl.tech'
EVENTSTREAM_ALLOW_CREDENTIALS = True
EVENTSTREAM_ALLOW_HEADERS = 'Authorization'

# PUSHPIN = os.getenv("PUSHPIN_HOST")
# GRIP_URL = f'http://{PUSHPIN}:5561'

# cache
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

CACHEOPS_DEFAULTS = {
    'timeout': 60*60*6,
}

CACHEOPS_REDIS = f"redis://{REDIS_HOST}:6379/2"

CACHEOPS = {
    'taskmanager.user': {'ops': ('get', 'fetch'), },
    'taskmanager.user_set': {'ops': ('get', 'fetch'), },
    'workspaces.workspace': {'ops': ('get', 'fetch'), },
    'workspaces.workspace_set': {'ops': ('get', 'fetch'), },
    'workspaces.board': {'ops': ('get', 'fetch'), },
    'workspaces.column': {'ops': ('get', 'fetch'), },
    'workspaces.column_set': {'ops': ('get', 'fetch'), },
    'workspaces.task': {'ops': ('get', 'fetch'), },
    'workspaces.task_set': {'ops': ('get', 'fetch'), },
    'workspaces.sticker': {'ops': ('get', 'fetch'), },
    'workspaces.sticker_set': {'ops': ('get', 'fetch'), },
}

START_BOT_LINK = 'https://t.me/PulseWaveBot?start='

# sentry logging
# SENTRY = os.getenv('SENTRY')
# PROJECT = os.getenv('PROJECT')

sentry_sdk.init(
    dsn="https://c2da026a69c4630d470e2a9c4030d907@o4506724974919680.ingest.sentry.io/4506751797231616",
    integrations=[
        LoggingIntegration(
            level=logging.ERROR,        # Capture info and above as breadcrumbs
            event_level=logging.ERROR   # Send records as events
        ),
    ],
)
