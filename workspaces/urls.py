from django.urls import path, include
from workspaces.views import UserList, WorkSpaceViewSet

from rest_framework import routers

router = routers.DefaultRouter()
router.register('workspace', WorkSpaceViewSet)


urlpatterns = [
    path('user_list/', UserList.as_view()),
]
urlpatterns += router.urls
