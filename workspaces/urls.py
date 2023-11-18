from django.urls import path, include
from workspaces.views import WorkSpaceViewSet, WorkSpaceViewSet

from rest_framework import routers

router = routers.DefaultRouter()
router.register('workspace', WorkSpaceViewSet)


urlpatterns = [
    # path('workspace/', WorkSpaceViewSet.as_view()),
    # path('workspace/list/', WorkSpaceView.as_view()),
]
urlpatterns += router.urls
