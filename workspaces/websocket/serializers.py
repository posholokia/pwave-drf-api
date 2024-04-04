from django.contrib.auth import get_user_model
from django.db import transaction

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from accounts.serializers import CurrentUserSerializer
from workspaces import mixins
from logic.indexing import index_recalculation
from workspaces.models import *
from workspaces.serializers import (CommentSerializer,
                                    StickerListSerializer,
                                    ColumnSerializer,
                                    )

User = get_user_model()


class TaskCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания задач"""
    sticker = serializers.SerializerMethodField()

    class Meta:
        model = Task
        read_only_fields = ['column', 'index', 'responsible', ]
        fields = (
            'id',
            'name',
            'index',
            'column',
            'responsible',
            'deadline',
            'description',
            # 'file',
            'priority',
            'sticker',
        )

    def create(self, validated_data):
        column_id = self.initial_data['column']
        number_of_tasks = Task.objects.filter(column_id=column_id).count()

        validated_data['index'] = number_of_tasks
        validated_data['column_id'] = column_id

        instance = Task.objects.create(**validated_data)
        return instance

    def get_sticker(self, obj):
        return []


class TaskUsersListSerializer(serializers.ListSerializer):
    def validate(self, attrs):
        task = self.parent.instance
        users = task.column.board.workspace.users.all().values_list('id', flat=True)
        for user_id in attrs:
            if user_id not in users:
                raise ValidationError(
                    {"responsible": f'Пользователь id:{user_id} не добавлен в рабочее пространство'},
                    'invalid_user'
                )
        print(f'{attrs=}')
        return attrs

    def to_representation(self, data):
        iterable = data.all()
        return [
            CurrentUserSerializer(item).data for item in iterable
        ]

class TaskSerializer(
    mixins.IndexValidateMixin,
    mixins.ColumnValidateMixin,
    serializers.ModelSerializer
):
    """Сериализатор задач"""
    responsible = TaskUsersListSerializer(child=serializers.IntegerField())
    comments = CommentSerializer(many=True, read_only=True)
    stickers = StickerListSerializer(many=True, read_only=True, source='sticker')

    class Meta:
        model = Task
        fields = (
            'id',
            'name',
            'index',
            'column',
            'responsible',
            'deadline',
            'description',
            # 'file',
            'priority',
            'comments',
            'stickers',
        )

    def validate(self, attrs):
        new_index = attrs.get('index', None)
        new_col = attrs.get('column', None)

        if (new_col is not None) and (self.instance.column != new_col):
            valid_columns = self.instance.column.board.column_board.all().values_list('id', flat=True)

            if new_col.id not in valid_columns:
                raise ValidationError(
                    {"column": 'Задачи можно перемещать только между колонками внутри доски'},
                    'invalid_column'
                )
            self.objects = new_col.task.all().order_by('index')
        else:
            new_col = None

        if new_index is not None:
            self.objects = self.index_validate(new_index, new_col)

        return attrs

    def update(self, instance, validated_data):
        """При перемещении задач их порядковые номера нужно пересчитать"""
        new_index = validated_data.get('index', None)
        new_col = validated_data.pop('column', None)
        users = validated_data.pop('responsible', None)

        with transaction.atomic():
            if users is not None:
                instance.responsible.set(users)
            if new_index is not None:
                instance = index_recalculation().shift(self.objects, instance, new_index, new_col)

            return super().update(instance, validated_data)


class BoardSerializer(serializers.ModelSerializer):
    """
    Сериализатор доски
    """
    columns = ColumnSerializer(many=True, read_only=True, source='column_board')

    class Meta:
        model = Board
        read_only_fields = ['members', 'workspace']
        fields = (
            'id',
            'name',
            'workspace',
            'members',
            'columns',
        )


class CreateBoardSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания доски
    """
    # workspace = serializers.PrimaryKeyRelatedField(queryset=WorkSpace.objects.all(), required=False)

    class Meta:
        model = Board
        fields = (
            'id',
            'name',
            'workspace',
        )

