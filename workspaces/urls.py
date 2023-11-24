from django.urls import path
from workspaces.views import UserList, WorkSpaceViewSet, TestSSEMessage, TestSSEUser, BoardViewSet

from rest_framework import routers

router = routers.DefaultRouter()
router.register('workspace', WorkSpaceViewSet)
router.register('boards', BoardViewSet)

urlpatterns = [
    path('user_list/', UserList.as_view()),
    path('sse_random_string/', TestSSEMessage.as_view()),
    path('sse_user/', TestSSEUser.as_view()),
]
urlpatterns += router.urls
