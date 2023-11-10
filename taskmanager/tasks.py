from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.utils import aware_utcnow
from celery import shared_task
from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task
def clear_expired_token():
    OutstandingToken.objects.filter(expires_at__lte=aware_utcnow()).delete()


@shared_task
def delete_inactive_user(user_id):
    user = User.objects.filter(id=user_id).first()
    if user and not user.is_active:
        user.delete()
