from datetime import timedelta

from django.utils.timezone import now
from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from pulsewave.settings import WORKSAPCES
from taskmanager.serializers import CurrentUserSerializer
from . import mixins
from .models import WorkSpace, Board, InvitedUsers, Task, Column

User = get_user_model()


class CreateWorkSpaceSerializer(serializers.ModelSerializer):
    """
    Сериализотор создания РП
    """
    # поле owner скрыто для редактирования и автоматически заполняется текущим пользователем
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = WorkSpace
        fields = (
            'owner',
            'name',
        )

    def create(self, validated_data):
        """
        При создании РП, пользователь, его создавший автоматически доабвляется
        в список пользователей РП
        """
        instance = super().create(validated_data)
        user = validated_data.get('owner')
        instance.users.add(user)
        return instance


class WorkspaceBoardsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Board
        fields = (
            'id',
            'name',
        )


class UserListWorkSpace(serializers.ModelSerializer):
    represent_name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        read_only_fields = ['email']
        fields = (
            'id',
            'email',
            'name',
            'represent_name',
            'avatar',
            'role',
        )

    def get_role(self, obj):
        workspace = self.context.get("workspace", None)

        if not workspace:
            return 'Invited'
        elif workspace.owner.id == obj.id:
            return 'Owner'
        else:
            return 'Member'

    def get_represent_name(self, obj):
        return obj.name if obj.name else obj.email.split('@')[0]


class WorkSpaceSerializer(serializers.ModelSerializer):
    boards = WorkspaceBoardsSerializer(many=True, read_only=True, source='board')
    users = serializers.SerializerMethodField()
    invited = UserListWorkSpace(many=True, read_only=True)

    class Meta:
        model = WorkSpace
        fields = (
            'id',
            'name',
            'users',
            'boards',
            'invited',
        )

    def get_users(self, obj):
        users_list = obj.users.all()
        users = UserListWorkSpace(users_list, many=True, read_only=True, context={'workspace': obj}).data
        return users


class WorkSpaceInviteSerializer(mixins.GetWorkSpaceMixin,
                                mixins.GetOrCreateUserMixin,
                                mixins.CheckWorkSpaceUsersMixin,
                                mixins.CheckWorkSpaceInvitedMixin,
                                serializers.Serializer):
    """
    Сериализотор пришлашения пользователей.
    Сериализует почту добавленного пользователя.
    """
    email = serializers.EmailField()

    default_error_messages = {
        'already_invited': 'Пользователь уже приглашен в это рабочее пространство',
        'already_added': 'Пользователь уже добавлен в это рабочее пространство',
    }

    def validate(self, attrs):
        user_email = attrs['email']
        self.workspace = self.get_workspace()
        self.user = self.get_or_create_user(user_email)

        if self.user_is_added_to_workspace():
            raise ValidationError(
                {"email": self.default_error_messages['already_added']},
                'already_added'
            )

        if self.user_is_invited_to_workspace():
            raise ValidationError(
                {"email": self.default_error_messages['already_invited']},
                'already_invited'
            )

        return attrs


class InviteUserSerializer(mixins.GetInvitedMixin,
                           mixins.CheckWorkSpaceUsersMixin,
                           mixins.CheckWorkSpaceInvitedMixin,
                           serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    default_error_messages = {
        'invalid_token': 'Недействительный токен',
        'token_expired': 'Срок действия токена истек',
        'already_invited': 'Пользователь уже был добавлен в это РП',
    }

    class Meta:
        model = InvitedUsers
        read_only_fields = ['user', 'workspace']
        fields = (
            'token',
            'user',
            'workspace',
        )

    def get_user(self, obj):
        return obj.user.email

    def validate(self, attrs):
        self.get_invitation(**attrs)

        time_out = timedelta(seconds=WORKSAPCES['INVITE_TOKEN_TIMEOUT'])
        expired_token = self.invitation.created_at + time_out

        if now() > expired_token:
            raise ValidationError(
                {"token": self.default_error_messages['token_expired']},
                'token_expired'
            )

        return attrs


class UserListSerializer(serializers.ModelSerializer):
    """
    Сериализатор списка пользователей при поиске.
    """

    name = serializers.SerializerMethodField()
    added = serializers.SerializerMethodField()
    invited = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'name',
            'email',
            'added',
            'invited',
        )

    def get_name(self, obj):
        return obj.representation_name()

    def get_added(self, obj):
        workspace_id = self.context.get('view').request.query_params.get('workspace')
        if obj.joined_workspaces.filter(id=workspace_id).exists():
            return True
        return False

    def get_invited(self, obj):
        workspace_id = self.context.get('view').request.query_params.get('workspace')
        if obj.invited_to_workspaces.filter(id=workspace_id).exists():
            return True
        return False


class UserIDSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()

    def validate(self, attrs):
        try:
            self.user = User.objects.get(pk=attrs['user_id'])
            return attrs
        except User.DoesNotExist:
            raise ValidationError(
                {"user_id": self.default_error_messages['invalid_user']},
                'invalid_user'
            )


class ResendInviteSerializer(mixins.GetWorkSpaceMixin,
                             mixins.CheckWorkSpaceUsersMixin,
                             mixins.CheckWorkSpaceInvitedMixin,
                             UserIDSerializer):
    """
    Сериализатор повторной отправки приглашения
    """
    default_error_messages = {
        'already_invited': 'Пользователь уже принял приглашение',
        'incorrect_invite': 'Пользователя нет в списке приглашенных в это РП',
        'invalid_user': 'Такого пользователя не существует',
    }

    def validate(self, attrs):
        attrs = super().validate(attrs)

        self.workspace = self.get_workspace()

        if self.user_is_added_to_workspace():
            raise ValidationError(
                {"user_id": self.default_error_messages['already_invited']},
                'already_invited'
            )

        if self.user_is_invited_to_workspace():
            return attrs

        raise ValidationError(
            {"user_id": self.default_error_messages["incorrect_invite"]},
            'incorrect_invite'
        )


class CreateBoardSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания доски
    """

    class Meta:
        model = Board
        fields = (
            'id',
            'name',
            'work_space',
        )


class TaskSerializer(serializers.ModelSerializer):
    """
    Сериализатор задачи
    """

    class Meta:
        model = Task
        fields = (
            'id',
            'name',
            'index',
            # 'column',
            # 'board',
        )


class ColumnSerializer(serializers.ModelSerializer):
    """
    Сериализатор задачи
    """
    tasks = TaskSerializer(many=True, read_only=True, source='task')

    class Meta:
        model = Column
        fields = (
            'id',
            'name',
            # 'board',
            'tasks',
        )


class BoardSerializer(serializers.ModelSerializer):
    """
    Сериализатор доски
    """
    members = CurrentUserSerializer(many=True, read_only=True)
    columns = ColumnSerializer(many=True, read_only=True, source='column_board')

    # tasks = TaskSerializer(many=True, read_only=True, source='task_board')

    class Meta:
        model = Board
        read_only_fields = ['work_space']
        fields = (
            'id',
            'name',
            'work_space',
            'members',
            'columns',
            # 'tasks',
        )
