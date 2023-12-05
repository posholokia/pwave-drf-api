from django.urls import path
from workspaces.views import UserList, WorkSpaceViewSet, TestSSEMessage, TestSSEUser, BoardViewSet, ColumnViewSet

from rest_framework import routers

router = routers.DefaultRouter()
router.register('column', ColumnViewSet, basename='column')
router.register('workspace', WorkSpaceViewSet, basename='workspace')
router.register('boards', BoardViewSet, basename='boards')


urlpatterns = [
    # path('boards/<int:board_pk>/column/', ColumnViewSet.as_view({'get': 'list'}), ),
    path('user_list/', UserList.as_view(), name='search_user'),
    path('sse_random_string/', TestSSEMessage.as_view()),
    path('sse_user/', TestSSEUser.as_view()),
]


urlpatterns += router.urls
