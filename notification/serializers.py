from rest_framework import serializers

from notification.models import Notification
from rest_framework.exceptions import ValidationError


class NotificationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = (
            'id',
            'text',
            'created_at',
            'read',
            'workspace',
            'board',
        )


class NotificationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = (
            'id',
            'read',
        )

    def validate(self, attrs):
        read = attrs.get('read', None)

        if read is not None:
            if read:
                return attrs
            else:
                raise ValidationError(
                    {'read': 'Статус уведомления нельзя изменить на "Не прочитано"'},
                    'invalid_read',
                )

        return {}
