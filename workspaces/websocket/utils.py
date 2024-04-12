from typing import Optional

from asgiref.sync import async_to_sync

from channels.layers import get_channel_layer

from logic.redis_layer import CustomRedisChannelLayer
from workspaces.database import get_board, get_task
from workspaces.models import Board, Task
from workspaces.websocket.serializers import BoardSerializer, TaskSerializer


def group_send_data(channel_layer: CustomRedisChannelLayer,
                    group_name: str,
                    data: dict | None,
                    exclude_channel: Optional[str] = None) -> None:
    """Рассылка сообщений всем каналам в группе"""
    async_to_sync(channel_layer.group_send)(
        group_name,
        {'type': 'message_send', 'data': data},
        exclude_channel=exclude_channel,
    )


def send_board_group_consumers(board_id: int) -> None:
    channel_layer = get_channel_layer()
    queryset = Board.objects.all()
    queryset = get_board(queryset)
    board = queryset.get(pk=board_id)

    data = BoardSerializer(board).data
    group_send_data(
        channel_layer,
        f'board-{board_id}',
        data,
    )


def send_task_group_consumers(task_id: int) -> None:
    channel_layer = get_channel_layer()
    queryset = Task.objects.all()
    queryset = get_task(queryset)
    task = queryset.get(pk=task_id)
    data = TaskSerializer(task).data

    group_send_data(
        channel_layer,
        f'task-{task_id}',
        data,
    )
