from datetime import timedelta
from django.utils.timezone import now
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from django.contrib.auth import get_user_model

from pulsewave.settings import WORKSAPCES
from taskmanager.serializers import CurrentUserSerializer
from . import mixins
from .models import WorkSpace, Board, InvitedUsers

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


class WorkSpaceSerializer(serializers.ModelSerializer):
    """
   Сериализотор РП
   """
    users = CurrentUserSerializer(many=True, read_only=True)
    invited = CurrentUserSerializer(many=True, read_only=True)

    class Meta:
        model = WorkSpace
        fields = (
            'id',
            'users',
            'invited',
            'name',
        )


class WorkSpaceInviteSerializer(mixins.GetWorkSpaceMixin,
                                serializers.Serializer):
    """
    Сериализотор пришлашения пользователей.
    Сериализует почту добавленного пользователя.
    """
    email = serializers.EmailField()


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
        self.get_invited_user(**attrs)

        time_out = timedelta(seconds=WORKSAPCES['INVITE_TOKEN_TIMEOUT'])
        expired_token = self.invited_user.created_at + time_out

        if now() > expired_token:
            raise ValidationError(
                {"token": self.default_error_messages['token_expired']},
                'token_expired'
            )

        self.workspace = self.invited_user.workspace
        self.user = self.invited_user.user

        if self.is_user_added():
            raise ValidationError(
                {"token": self.default_error_messages['already_invited']},
                'already_invited'
            )

        if self.is_user_invited():
            return attrs

        raise ValidationError(
            {"token": self.default_error_messages['invalid_token']},
            'invalid_token'
        )


class UserListSerializer(serializers.ModelSerializer):
    """
    Сериализатор списка пользователей при поиске.
    """
    class Meta:
        model = User
        fields = (
            'name',
            'email',
            'id',
        )


class UserIDSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()


class ResendInviteSerializer(mixins.GetUserMixin,
                             mixins.GetWorkSpaceMixin,
                             mixins.CheckWorkSpaceUsersMixin,
                             mixins.CheckWorkSpaceInvitedMixin,
                             UserIDSerializer):
    default_error_messages = {
        'already_invited': 'Пользователь уже принял приглашение',
        'incorrect_invite': 'Пользователя нет в списке приглашенных в это РП',
        'invalid_user': 'Такого пользователя не существует',
    }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        user_id = attrs['user_id']

        self.get_workspace()
        self.get_user_object(pk=user_id)

        self.is_user_added()

        if self.is_user_invited():
            return attrs

        raise ValidationError(
            {"user_id": self.default_error_messages["incorrect_invite"]},
            'incorrect_invite'
        )


class BoardSerializer(serializers.ModelSerializer):
    members = CurrentUserSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = (
            'name',
            'members',
            'id',
        )
