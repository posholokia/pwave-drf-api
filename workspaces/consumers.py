import json

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from django.db.models import Prefetch
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework import mixins
from djangochannelsrestframework.observer.generics import (ObserverModelInstanceMixin, action)
from djangochannelsrestframework.observer import model_observer

from . import serializers
from .models import Task, Sticker, Comment
from .serializers import TaskListSerializer, StickerListSerializer, TaskSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class TaskConsumer(mixins.CreateModelMixin,
                   mixins.PatchModelMixin,
                   ObserverModelInstanceMixin,
                   GenericAsyncAPIConsumer):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    lookup_field = "pk"

    def get_serializer_class(self, **kwargs):
        if kwargs.get('action') == 'create':
            return serializers.TaskCreateSerializer
        elif kwargs.get('action') == 'list':
            return serializers.TaskListSerializer

        return super().get_serializer_class()

    def get_queryset(self, **kwargs):
        """Задачи фильтруются по колонкам"""
        queryset = super().get_queryset()
        # print(f'\n{kwargs}=')
        # column_id = kwargs.get('column', None)
        # print(f'\n\n{column_id=}')
        #
        # queryset = queryset.filter(column_id=column_id)
        # queryset = (queryset
        #             .prefetch_related('responsible')
        #             .prefetch_related(Prefetch('sticker',
        #                                        queryset=Sticker.objects.order_by('id')))
        #             .prefetch_related(Prefetch('comments',
        #                                        queryset=Comment.objects.order_by('id')))
        #             )

        return queryset.order_by('index')

    @action()
    async def subscribe_to_task(self, pk, **kwargs):
        await self.task_activity.subscribe(id=pk)
        await self.sticker_activity.subscribe(sticker__id=pk)

    @model_observer(Task)
    async def task_activity(self, task, observer=None, **kwargs):
        await self.send_json(task)

    @task_activity.serializer
    def task_activity(self, instance: Task, action, **kwargs):
        return TaskListSerializer(instance).data

    @model_observer(Sticker)
    async def sticker_activity(self, task, observer=None, **kwargs):
        await self.send_json(task)

    @sticker_activity.serializer
    def sticker_activity(self, instance: Sticker, action, **kwargs):
        return TaskListSerializer(instance.task).data
