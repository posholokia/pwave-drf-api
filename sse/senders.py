from django.db.models import Prefetch

from django_eventstream import send_event

from celery import shared_task

from notification.serializers import NotificationListSerializer
from workspaces.models import Board, Task, Sticker, Comment
from workspaces.serializers import BoardSerializer, TaskSerializer


def sse_send_notifications(obj, pks):
    data = NotificationListSerializer(obj).data
    for pk in pks:
        send_event(
            f'user-{pk}',
            'notification',
            data
        )


@shared_task
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
    data['exclude_user'] = args[1].user.id
    send_event(
        f'board-{bord_id}',
        'board',
        data,
    )


@shared_task
def sse_send_task(task_id, *args):
    sticker_prefetch = Prefetch(
        'sticker',
        queryset=Sticker.objects.order_by('id')
    )
    comment_prefetch = Prefetch(
        'comments',
        queryset=Comment.objects.order_by('id')
    )
    task = (Task.objects
            .prefetch_related('responsible')
            .prefetch_related(sticker_prefetch)
            .prefetch_related(comment_prefetch)
            .get(pk=task_id)
            )

    data = TaskSerializer(
        task,
        context={'request': args[1], 'view': args[0]},
    ).data
    data['exclude_user'] = args[1].user.id
    send_event(
        f'task-{task_id}',
        'task',
        data,
    )
