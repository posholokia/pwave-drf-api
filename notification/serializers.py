from rest_framework import serializers

from notification.models import Notification
from rest_framework.exceptions import ValidationError

from workspaces.models import WorkSpace, Board


class WorkSpaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkSpace
        fields = (
            'id',
            'name',
        )


class BoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = (
            'id',
            'work_space',
            'name',
        )


class NotificationListSerializer(serializers.ModelSerializer):
    workspace = WorkSpaceSerializer(read_only=True)
    board = BoardSerializer(read_only=True)

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
