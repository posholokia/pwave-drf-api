from django.urls import path
from rest_framework import routers
from .views import *


urlpatterns = [
    path('change_email/', ChangeEmailView.as_view()),
    path('change_email_confirm/', ChangeEmailConfirmView.as_view()),
]

