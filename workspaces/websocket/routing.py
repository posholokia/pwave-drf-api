from django.urls import path

from workspaces.websocket import consumers

websocket_urlpatterns = [
    # re_path(r'^ws/task/(?P<pk>\d+)/$', consumers.TaskConsumer.as_asgi()),
    path('ws/task/', consumers.TaskConsumer.as_asgi()),
    path('ws/board/', consumers.BoardConsumer.as_asgi()),
]
