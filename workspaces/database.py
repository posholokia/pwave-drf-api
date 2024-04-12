from django.db.models import Prefetch

from workspaces.models import Column, Task, Sticker, Comment


def get_board(queryset):
    queryset = (queryset
                .prefetch_related('members')
                .prefetch_related(
                    Prefetch('column_board',
                             queryset=Column.objects.order_by('index'),
                             ))
                .prefetch_related(
                    Prefetch('column_board__task',
                             queryset=Task.objects.order_by('index'),
                             ))
                .prefetch_related('column_board__task__responsible')
                .prefetch_related(
                    Prefetch('column_board__task__sticker',
                             queryset=Sticker.objects.order_by('id'))
                ))
    return queryset


def get_task(queryset):
    queryset = (queryset
                .prefetch_related('responsible')
                .prefetch_related(Prefetch('sticker',
                                           queryset=Sticker.objects.order_by('id')))
                .prefetch_related(Prefetch('comments',
                                           queryset=Comment.objects.order_by('id')))
                )
    return queryset
