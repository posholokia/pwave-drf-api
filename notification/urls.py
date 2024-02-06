from django.urls import path
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register('', NotificationList, basename='notification-list')


urlpatterns = [
    path('<int:pk>/read/', NotificationUpdate.as_view(), name='notification-update'),
]

urlpatterns += router.urls
