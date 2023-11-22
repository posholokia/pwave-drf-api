from django.urls import path, include
from workspaces.views import UserList, WorkSpaceViewSet, TestSSEMessage, TestSSEUser

from rest_framework import routers

router = routers.DefaultRouter()
router.register('workspace', WorkSpaceViewSet)


urlpatterns = [
    path('user_list/', UserList.as_view()),
    path('sse_random_string/', TestSSEMessage.as_view()),
    path('sse_user/', TestSSEUser.as_view()),
]
urlpatterns += router.urls
