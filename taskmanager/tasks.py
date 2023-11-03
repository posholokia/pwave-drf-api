from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.utils import aware_utcnow
from celery import shared_task


@shared_task
def clear_expired_token():
    OutstandingToken.objects.filter(expires_at__lte=aware_utcnow()).delete()



