from django.db.models import Prefetch

from workspaces.models import Column, Task, Sticker


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
