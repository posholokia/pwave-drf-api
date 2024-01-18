from django.urls import path

from .views import *


urlpatterns = [
    path('notification/', NotificationList.as_view(), name='notification-list'),
    path('notification/<int:pk>/read/', NotificationUpdate.as_view(), name='notification-update'),

]

