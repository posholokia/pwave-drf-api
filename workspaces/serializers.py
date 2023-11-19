from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from django.contrib.auth import get_user_model

from djoser import utils
from djoser.serializers import PasswordRetypeSerializer

from taskmanager.token import user_token_generator
from .models import WorkSpace

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

    class Meta:
        model = WorkSpace
        fields = (
            'users',
            'invited',
            'name',
        )


class WorkSpaceInviteSerializer(serializers.Serializer):
    """
    Сериализотор пришлашения пользователей.
    Сериализует почту добавленного пользователя.
    """
    email = serializers.EmailField()


class WuidUidTokenSerializer(serializers.Serializer):
    """
    Сериализатор уникальных идентификаторов.
    wuid: идентификатор РП
    uid: идентификатор пользователя
    token: токен пользователя
    """
    wuid = serializers.CharField()
    uid = serializers.CharField()
    token = serializers.CharField()

    default_error_messages = {
        "invalid_token": 'Некорректный токен',
        "invalid_uid": 'Нет пользователя с таким uid',
        "invalid_wuid": 'Нет рабочего простанства с таким wuid',
        "invite_invalid": "Приглашение в это рабочее пространство уже не актуально"
    }

    def validate(self, attrs):
        """
        Валидация полученных данных.
        Сперва пытается получить РП из wuid.
        Затем пользователя из uid.
        Затем проверяет действительность токена для текущего пользователя.
        """
        validated_data = super().validate(attrs)

        try:
            wuid = utils.decode_uid(self.initial_data.get("wuid", ""))
            self.workspace = WorkSpace.objects.get(pk=wuid)
        except (WorkSpace.DoesNotExist, ValueError, TypeError, OverflowError):
            raise ValidationError(
                {"wuid": self.default_error_messages["invalid_wuid"]},
                'invalid_wuid'
            )

        try:
            uid = utils.decode_uid(self.initial_data.get("uid", ""))
            self.user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            key_error = "invalid_uid"
            raise ValidationError(
                {"uid": [self.error_messages[key_error]]},
                'invalid_uid'
            )

        is_token_valid = user_token_generator.check_token(
            self.user, self.initial_data.get("token", "")
        )

        if is_token_valid:
            if self.user in self.workspace.invited.filter(id=self.user.id):
                return validated_data

            raise ValidationError(
                {"detail": self.error_messages['invite_invalid']},
                'invite_invalid'
            )

        else:
            key_error = "invalid_token"
            raise ValidationError(
                {"token": [self.error_messages[key_error]]}, code=key_error
            )


class InviteUserSerializer(WuidUidTokenSerializer):
    """
    Сериализатор приглашенного пользователя, который был зарегистрирвоан на момент приглашения.
    """
    pass


class InviteNewUserSerializer(WuidUidTokenSerializer, PasswordRetypeSerializer):
    """
    Сериализатор приглашенного пользователя, который не был зарегистрирвоан на момент приглашения.
    """
    pass


class UserListSerializer(serializers.ModelSerializer):
    """
    Сериализатор списка пользователей при поиске.
    """
    class Meta:
        model = User
        fields = (
            'email',
            'id',
        )
