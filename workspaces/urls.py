from django.urls import path
from workspaces.views import UserList, WorkSpaceViewSet, TestSSEMessage, TestSSEUser, BoardViewSet, ColumnViewSet
from rest_framework import routers

router = routers.DefaultRouter()
router.register('workspace', WorkSpaceViewSet, basename='workspace')
router.register('boards', BoardViewSet, basename='boards')
router.register(r'boards/(?P<board_pk>\d+)/column', ColumnViewSet, basename='column')


urlpatterns = [
    path('user_list/', UserList.as_view(), name='search_user'),
    path('sse_random_string/', TestSSEMessage.as_view()),
    path('sse_user/', TestSSEUser.as_view()),
]


urlpatterns += router.urls
