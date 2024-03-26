from django.urls import path, re_path

from . import consumers


websocket_urlpatterns = [
    path("ws/task/", consumers.TaskConsumer.as_asgi()),
    # path('ws/chat/', consumers.RoomConsumer.as_asgi()),
]