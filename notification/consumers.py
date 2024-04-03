from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework import mixins
from djangochannelsrestframework.observer.generics import (ObserverModelInstanceMixin, action)
from djangochannelsrestframework.observer import model_observer

from rest_framework import status

from notification.models import Notification
from workspaces.websocket.permissions import IsAuthenticated
from .serializers import NotificationListSerializer, NotificationUpdateSerializer


class NotificationConsumer(mixins.ListModelMixin,
                           mixins.PatchModelMixin,
                           ObserverModelInstanceMixin,
                           GenericAsyncAPIConsumer):
    queryset = Notification.objects.all()
    serializer_class = NotificationListSerializer
    lookup_field = "pk"
    permission_classes = [IsAuthenticated, ]

    def get_serializer_class(self, **kwargs):
        if (kwargs.get('action') == 'patch' or
                kwargs.get('action') == 'read_all'):
            return NotificationUpdateSerializer

        return super().get_serializer_class(**kwargs)

    def get_queryset(self, **kwargs):
        queryset = super().get_queryset()
        user = self.scope['user']
        queryset = queryset.filter(recipients=user)
        return queryset.order_by('-created_at')[:25]

    async def connect(self):
        await self.notification_activity.subscribe()
        await self.accept()

    @model_observer(Notification, serializer_class=NotificationListSerializer)
    async def notification_activity(self,
                                    notification,
                                    observer=None,
                                    **kwargs):
        await self.reply(notification)

    @action()
    def read_all(self, **kwargs):
        user = self.scope['user']
        queryset = Notification.objects.filter(
            recipients=user, read=False,
        )
        queryset.update(read=True)
        return (NotificationListSerializer(
            self.get_queryset(), many=True,
        ).data, status.HTTP_200_OK)

