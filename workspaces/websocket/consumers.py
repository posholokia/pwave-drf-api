from typing import Tuple

from django.contrib.auth import get_user_model

from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework import mixins
from djangochannelsrestframework.observer.generics import action

from rest_framework import status

from logic.indexing import index_recalculation
from notification.create_notify.decorators import task_notification
from ..database import get_board, get_task
from ..mixins import ConsumerMixin
from .utils import group_send_data, send_board_group_consumers
from workspaces.websocket import serializers
from workspaces.models import Task, Board
from .permissions import IsAuthenticated, ThisTaskInUserWorkspace, UserInWorkSpaceUsers

User = get_user_model()


class TaskConsumer(mixins.CreateModelMixin,
                   mixins.PatchModelMixin,
                   mixins.DeleteModelMixin,
                   mixins.RetrieveModelMixin,
                   ConsumerMixin,
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
        queryset = get_task(
            super().get_queryset()
        )
        return queryset.order_by('index')

    @action()
    def create(self, data: dict, **kwargs):
        serializer = self.get_serializer(data=data, action_kwargs=kwargs)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer, **kwargs)

        board_id = serializer.instance.column.board_id
        send_board_group_consumers(board_id)

        return serializer.data, status.HTTP_201_CREATED

    @action()
    @task_notification
    def patch(self, data: dict, **kwargs):
        instance = self.get_object(data=data, **kwargs)
        serializer = self.get_serializer(
            instance=instance, data=data, action_kwargs=kwargs, partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_patch(serializer, **kwargs)

        board_id = instance.column.board_id
        send_board_group_consumers(board_id)
        group_send_data(self.channel_layer,
                        self.group_name,
                        serializer.data,
                        self.channel_name)

        return serializer.data, status.HTTP_200_OK

    @action()
    @task_notification
    def delete(self, **kwargs) -> Tuple[None, int]:
        instance = self.get_object(**kwargs)
        board_id = instance.column.board_id
        index_recalculation().delete_shift_index(instance)
        self.perform_delete(instance, **kwargs)

        send_board_group_consumers(board_id)
        group_send_data(self.channel_layer,
                        self.group_name,
                        None,
                        self.channel_name)

        return None, status.HTTP_204_NO_CONTENT


class BoardConsumer(mixins.CreateModelMixin,
                    mixins.PatchModelMixin,
                    mixins.DeleteModelMixin,
                    mixins.RetrieveModelMixin,
                    ConsumerMixin,
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
        queryset = get_board(
            super().get_queryset()
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
        Метод обновления задачи
        """
        instance = self.get_object(data=data, **kwargs)
        serializer = self.get_serializer(
            instance=instance, data=data, action_kwargs=kwargs, partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_patch(serializer, **kwargs)

        group_send_data(self.channel_layer,
                        self.group_name,
                        serializer.data,
                        self.channel_name)

        return serializer.data, status.HTTP_200_OK

    @action()
    def delete(self, **kwargs) -> Tuple[None, int]:
        instance = self.get_object(**kwargs)
        self.perform_delete(instance, **kwargs)

        group_send_data(self.channel_layer,
                        self.group_name,
                        None,
                        self.channel_name)

        return None, status.HTTP_204_NO_CONTENT
