from django.urls import path

from .views import *


urlpatterns = [
    path('', NotificationList.as_view(), name='notification-list'),
    path('<int:pk>/read/', NotificationUpdate.as_view(), name='notification-update'),

]

