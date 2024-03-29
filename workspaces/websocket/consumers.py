from typing import Tuple

from django.db.models import Prefetch
from django.contrib.auth import get_user_model

from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework import mixins
from djangochannelsrestframework.observer.generics import (ObserverModelInstanceMixin, action)
from djangochannelsrestframework.observer import model_observer

from rest_framework import status

from logic.indexing import index_recalculation
from workspaces import serializers
from workspaces.models import Task, Sticker, Comment
from workspaces.serializers import TaskSerializer
from .permissions import IsAuthenticated, ThisTaskInUserWorkspace

User = get_user_model()


class TaskConsumer(mixins.CreateModelMixin,
                   mixins.PatchModelMixin,
                   ObserverModelInstanceMixin,
                   mixins.DeleteModelMixin,
                   GenericAsyncAPIConsumer):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    lookup_field = "pk"
    permission_classes = [IsAuthenticated, ThisTaskInUserWorkspace, ]

    def disconnect(self, code):
        return super().disconnect(code)

    def get_serializer_class(self, **kwargs):
        if kwargs.get('action') == 'create':
            return serializers.TaskCreateSerializer
        elif kwargs.get('action') == 'retrieve':
            return serializers.TaskSerializer

        return super().get_serializer_class()

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
    async def subscribe_to_task(self, pk, request_id, **kwargs):
        await self.task_activity.subscribe(task=pk, request_id=request_id)
        await self.sticker_activity.subscribe(task=pk, request_id=request_id)
        await self.comment_activity.subscribe(task=pk, request_id=request_id)

    @action()
    async def unsubscribe_to_task(self, pk, **kwargs):
        await self.task_activity.unsubscribe(task=pk)
        await self.sticker_activity.unsubscribe(task=pk)
        await self.comment_activity.unsubscribe(task=pk)

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
    def task_activity(self, task: Task, action, **kwargs):
        return TaskSerializer(task).data

    @model_observer(Sticker)
    async def sticker_activity(self, task, observer=None, **kwargs):
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
        return TaskSerializer(instance.task).data

    @model_observer(Comment)
    async def comment_activity(self, task, observer=None, **kwargs):
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
        return TaskSerializer(instance.task).data
