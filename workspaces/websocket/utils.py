from typing import Optional

from asgiref.sync import async_to_sync

from channels.layers import get_channel_layer

from logic.redis_layer import CustomRedisChannelLayer
from workspaces.database import get_board
from workspaces.models import Board
from workspaces.websocket.serializers import BoardSerializer


def group_send_data(channel_layer: CustomRedisChannelLayer,
                    group_name: str,
                    data: dict | None,
                    exclude_channel: Optional[str] = None):
    """Рассылка сообщений всем каналам в группе"""
    async_to_sync(channel_layer.group_send)(
        group_name,
        {'type': 'message_send', 'data': data},
        exclude_channel=exclude_channel,
    )


def send_board_group_consumers(board_id):
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
