from rest_framework import viewsets, permissions, status, generics
from . import serializers
from .models import Notification


class NotificationList(generics.ListAPIView):
    serializer_class = serializers.NotificationListSerializer
    queryset = Notification.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        queryset = queryset.filter(recipients=user)
        return queryset.order_by('-created_at')[:25]


class NotificationUpdate(generics.UpdateAPIView):
    serializer_class = serializers.NotificationUpdateSerializer
    queryset = Notification.objects.all()
    permission_classes = [permissions.IsAuthenticated]

