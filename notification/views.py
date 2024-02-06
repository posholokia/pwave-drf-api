from rest_framework import viewsets, permissions, generics
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin

from . import serializers
from .models import Notification
from rest_framework.response import Response


class NotificationList(ListModelMixin,
                       viewsets.GenericViewSet):
    serializer_class = serializers.NotificationListSerializer
    queryset = Notification.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        queryset = queryset.filter(recipients=user)
        return queryset.order_by('-created_at')[:25]

    @action(methods=['patch'], detail=False, url_name='read_all_notification')
    def read_all(self, request, *args, **kwargs):
        queryset = self.queryset.filter(
            recipients=self.request.user,
            read=False,
        )
        queryset.update(read=True)
        data = self.serializer_class(self.get_queryset(), many=True).data
        return Response(data)


class NotificationUpdate(generics.UpdateAPIView):
    serializer_class = serializers.NotificationUpdateSerializer
    queryset = Notification.objects.all()
    permission_classes = [permissions.IsAuthenticated]
