import datetime

from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from django.urls import reverse
from freezegun import freeze_time

from notification.models import Notification
from workspaces.models import WorkSpace, Board, Column, Task

User = get_user_model()


class NotificationTestCase(APITestCase):
    # TODO переписать под вебсокеты
    pass
