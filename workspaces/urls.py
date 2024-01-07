from django.urls import path
from workspaces.views import *
from rest_framework import routers

router = routers.DefaultRouter()
router.register('workspace', WorkSpaceViewSet, basename='workspace')
router.register(r'workspace/(?P<workspace_id>\d+)/boards', BoardViewSet, basename='boards')
router.register(r'boards/(?P<board_id>\d+)/column', ColumnViewSet, basename='column')
router.register(r'column/(?P<column_id>\d+)/task', TaskViewSet, basename='task')
router.register(r'task/(?P<task_id>\d+)/sticker', StickerViewSet, basename='sticker')


urlpatterns = [
    path('user_list/', UserList.as_view(), name='search_user'),
    path('board_create/', BoardCreateWithoutWorkSpace.as_view(), name='out_ws_create_board'),
    path('sse_random_string/', TestSSEMessage.as_view()),
    path('sse_user/', TestSSEUser.as_view()),
    path('index_fixed/', index_columns),
    path('ws/', return_ws),
]

urlpatterns += router.urls
