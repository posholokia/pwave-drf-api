from django_eventstream import send_event

from notification.serializers import NotificationListSerializer
from workspaces.models import Board, Task
from workspaces.serializers import BoardSerializer, TaskSerializer


def sse_send_notifications(obj, pks):
    data = NotificationListSerializer(obj).data
    for pk in pks:
        send_event(
            f'user-{pk}',
            'notification',
            data
        )


def sse_send_board(bord_id, *args):
    board = (Board.objects
             .prefetch_related('members')
             .prefetch_related('column_board')
             .prefetch_related('column_board__task')
             .prefetch_related('column_board__task__responsible')
             .prefetch_related('column_board__task__sticker')
             .get(pk=bord_id)
             )
    data = BoardSerializer(
        board,
        context={'request': args[1], 'view': args[0]},
    ).data
    send_event(
        f'board-{bord_id}',
        'board',
        data,
    )


def sse_send_task(task_id, *args):
    task = (Task.objects
            .prefetch_related('responsible')
            .prefetch_related('sticker')
            .prefetch_related('comments')
            .get(pk=task_id)
            )
    data = TaskSerializer(
        task,
        context={'request': args[1], 'view': args[0]},
    ).data
    send_event(
        f'task-{task_id}',
        'task',
        data,
    )
