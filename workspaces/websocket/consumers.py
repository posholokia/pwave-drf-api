from typing import Tuple

from django.db.models import Prefetch
from django.contrib.auth import get_user_model

from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework import mixins
from djangochannelsrestframework.observer.generics import (ObserverModelInstanceMixin, action)
from djangochannelsrestframework.observer import model_observer

from rest_framework import status

from logic.indexing import index_recalculation
from workspaces.websocket import serializers
from workspaces.models import Task, Sticker, Comment, Board, Column
from .permissions import IsAuthenticated, ThisTaskInUserWorkspace, UserInWorkSpaceUsers
from ..serializers import BoardSerializer
from notification.create_notify.decorators import send_notify
from notification.create_notify.tasks import run_task_notification
from notification.create_notify.utils import get_pre_inintial_data

User = get_user_model()


class TaskConsumer(mixins.CreateModelMixin,
                   mixins.PatchModelMixin,
                   mixins.DeleteModelMixin,
                   ObserverModelInstanceMixin,
                   GenericAsyncAPIConsumer):
    queryset = Task.objects.all()
    serializer_class = serializers.TaskSerializer
    lookup_field = "pk"
    permission_classes = [IsAuthenticated, ThisTaskInUserWorkspace, ]

    def get_serializer_class(self, **kwargs):
        if kwargs.get('action') == 'create':
            return serializers.TaskCreateSerializer
        elif kwargs.get('action') == 'retrieve':
            return serializers.TaskSerializer

        return super().get_serializer_class(**kwargs)

    def get_queryset(self, **kwargs):
        queryset = super().get_queryset()
        queryset = (queryset
                    .prefetch_related('responsible')
                    .prefetch_related(Prefetch('sticker',
                                               queryset=Sticker.objects.order_by('id')))
                    .prefetch_related(Prefetch('comments',
                                               queryset=Comment.objects.order_by('id')))
                    )

        return queryset

    @action()
    async def subscribe(self, pk, request_id, **kwargs):
        await self.task_activity.subscribe(task=pk, request_id=request_id)
        await self.sticker_activity.subscribe(task=pk, request_id=request_id)
        await self.comment_activity.subscribe(task=pk, request_id=request_id)

    @action()
    async def unsubscribe(self, pk, **kwargs):
        await self.task_activity.unsubscribe(task=pk)
        await self.sticker_activity.unsubscribe(task=pk)
        await self.comment_activity.unsubscribe(task=pk)

    @action()
    def create(self, data: dict, **kwargs):
        serializer = self.get_serializer(data=data, action_kwargs=kwargs)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer, **kwargs)
        return serializer.data, status.HTTP_201_CREATED

    @action()
    def patch(self, data: dict, **kwargs):
        instance = self.get_object(data=data, **kwargs)
        serializer = self.get_serializer(
            instance=instance, data=data, action_kwargs=kwargs, partial=True
        )
        serializer.is_valid(raise_exception=True)

        # формирование уведомления
        # сохраняем текущую задачу и пользователя в словаре
        user, old_task = get_pre_inintial_data(self.scope['user'], instance.pk)
        self.perform_patch(serializer, **kwargs)
        # после обновления задачи отправляет в celery формировать уведомление
        run_task_notification.apply_async(
            (old_task, user, data)
        )
        return serializer.data, status.HTTP_200_OK

    @send_notify
    @action()
    def delete(self, **kwargs) -> Tuple[None, int]:
        instance = self.get_object(**kwargs)
        index_recalculation().delete_shift_index(instance)
        self.perform_delete(instance, **kwargs)
        return None, status.HTTP_204_NO_CONTENT

    @model_observer(Task)
    async def task_activity(self, task, observer=None, subscribing_request_ids=[], **kwargs):
        for request_id in subscribing_request_ids:
            await self.send_json(task)

    @task_activity.groups_for_consumer
    def task_activity(self, task: int = None, request_id=None, **kwargs):
        if task is not None:
            yield f'ws_task_group_{task}'

    @task_activity.groups_for_signal
    def task_activity(self, instance: Task = None, **kwargs):
        if instance is not None:
            yield f'ws_task_group_{instance.id}'

    @task_activity.serializer
    def task_activity(self, instance, action, **kwargs):
        return serializers.TaskSerializer(instance).data

    @model_observer(Sticker)
    async def sticker_activity(self, task, observer=None, subscribing_request_ids=[], **kwargs):
        for request_id in subscribing_request_ids:
            await self.send_json(task)

    @sticker_activity.groups_for_consumer
    def sticker_activity(self, task: Task = None, **kwargs):
        if task is not None:
            yield f'ws_task_group_{task}'

    @sticker_activity.groups_for_signal
    def sticker_activity(self, instance: Sticker = None, **kwargs):
        if instance is not None:
            yield f'ws_task_group_{instance.task_id}'

    @sticker_activity.serializer
    def sticker_activity(self, instance: Sticker, action, **kwargs):
        return serializers.TaskSerializer(instance.task).data

    @model_observer(Comment)
    async def comment_activity(self, task, observer=None, subscribing_request_ids=[], **kwargs):
        for request_id in subscribing_request_ids:
            await self.send_json(task)

    @comment_activity.groups_for_consumer
    def comment_activity(self, task: Task = None, **kwargs):
        if task is not None:
            yield f'ws_task_group_{task}'

    @comment_activity.groups_for_signal
    def comment_activity(self, instance: Comment = None, **kwargs):
        if instance is not None:
            yield f'ws_task_group_{instance.task_id}'

    @comment_activity.serializer
    def comment_activity(self, instance: Comment, action, **kwargs):
        return serializers.TaskSerializer(instance.task).data


class BoardConsumer(mixins.CreateModelMixin,
                    mixins.PatchModelMixin,
                    mixins.DeleteModelMixin,
                    ObserverModelInstanceMixin,
                    GenericAsyncAPIConsumer):
    queryset = Board.objects.all()
    serializer_class = serializers.BoardSerializer
    lookup_field = "pk"
    permission_classes = [IsAuthenticated, UserInWorkSpaceUsers, ]

    def get_serializer_class(self, **kwargs):
        if kwargs.get('action') == 'create':
            return serializers.CreateBoardSerializer

        return super().get_serializer_class()

    def get_queryset(self, **kwargs):
        queryset = (
            super().get_queryset()
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
            )
        )

        return queryset.order_by('id')

    @action()
    def create(self, data: dict, **kwargs):
        workspace_id = data.get('workspace')
        serializer = self.get_serializer(data=data, action_kwargs=kwargs)
        serializer.is_valid(raise_exception=True)

        if Board.objects.filter(workspace_id=workspace_id).count() >= 10:
            data = {'detail': 'Возможно создать не более 10 Досок'}
            return data, status.HTTP_400_BAD_REQUEST

        self.perform_create(serializer, **kwargs)
        return serializer.data, status.HTTP_201_CREATED

    @action()
    def patch(self, data: dict, **kwargs):
        """
        Удалена django валидация кэша.
        Иначе сортировка объектов рандомная
        """
        instance = self.get_object(data=data, **kwargs)
        serializer = self.get_serializer(
            instance=instance, data=data, action_kwargs=kwargs, partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_patch(serializer, **kwargs)
        return serializer.data, status.HTTP_200_OK

    @action()
    async def subscribe(self, pk, request_id, **kwargs):
        await self.board_activity.subscribe(instance=pk, request_id=request_id)
        await self.column_activity.subscribe(board=pk, request_id=request_id)
        await self.task_activity.subscribe(board=pk, request_id=request_id)
        await self.sticker_activity.subscribe(board=pk, request_id=request_id)

    @action()
    async def unsubscribe(self, pk, **kwargs):
        await self.board_activity.subscribe(instance=pk)
        await self.column_activity.unsubscribe(board=pk)
        await self.task_activity.unsubscribe(board=pk)
        await self.sticker_activity.unsubscribe(board=pk)

    @model_observer(Board)
    async def board_activity(self, board, observer=None, subscribing_request_ids=[], **kwargs):
        for request_id in subscribing_request_ids:
            await self.send_json(board)

    @board_activity.groups_for_consumer
    def board_activity(self, board: int = None, request_id=None, **kwargs):
        if board is not None:
            yield f'ws_board_group_{board}'

    @board_activity.groups_for_signal
    def board_activity(self, instance: Task = None, **kwargs):
        if instance is not None:
            yield f'ws_board_group_{instance.id}'

    @board_activity.serializer
    def board_activity(self, board: Board, action, **kwargs):
        return BoardSerializer(board).data

    @model_observer(Column)
    async def column_activity(self, board, observer=None, subscribing_request_ids=[], **kwargs):
        for request_id in subscribing_request_ids:
            await self.send_json(board)

    @column_activity.groups_for_consumer
    def column_activity(self, board: int = None, request_id=None, **kwargs):
        if board is not None:
            yield f'ws_board_group_{board}'

    @column_activity.groups_for_signal
    def column_activity(self, instance: Column = None, **kwargs):
        if instance is not None:
            yield f'ws_board_group_{instance.board_id}'

    @column_activity.serializer
    def column_activity(self, column: Column, action, **kwargs):
        return BoardSerializer(column.board).data

    @model_observer(Task)
    async def task_activity(self, board, observer=None, subscribing_request_ids=[], **kwargs):
        for request_id in subscribing_request_ids:
            await self.send_json(board)

    @task_activity.groups_for_consumer
    def task_activity(self, board: int = None, request_id=None, **kwargs):
        if board is not None:
            yield f'ws_board_group_{board}'

    @task_activity.groups_for_signal
    def task_activity(self, instance: Task = None, **kwargs):
        if instance is not None:
            yield f'ws_board_group_{instance.column.board_id}'

    @task_activity.serializer
    def task_activity(self, task: Task, action, **kwargs):
        return BoardSerializer(task.column.board).data

    @model_observer(Sticker)
    async def sticker_activity(self, board, observer=None, subscribing_request_ids=[], **kwargs):
        for request_id in subscribing_request_ids:
            await self.send_json(board)

    @sticker_activity.groups_for_consumer
    def sticker_activity(self, board: int = None, request_id=None, **kwargs):
        if board is not None:
            yield f'ws_board_group_{board}'

    @sticker_activity.groups_for_signal
    def sticker_activity(self, instance: Sticker = None, **kwargs):
        if instance is not None:
            yield f'ws_board_group_{instance.task.column.board_id}'

    @sticker_activity.serializer
    def sticker_activity(self, sticker: Sticker, action, **kwargs):
        return BoardSerializer(sticker.task.column.board).data
