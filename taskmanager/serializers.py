from rest_framework import serializers
from rest_framework import exceptions
from rest_framework_simplejwt.serializers import TokenObtainSerializer, TokenObtainPairSerializer
from rest_framework_simplejwt.settings import api_settings
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from djoser.serializers import SendEmailResetSerializer
from djoser.conf import settings as djoser_settings

User = get_user_model()


class CurrentUserSerializer(serializers.ModelSerializer):
    """
    Сериализатор пользователя, используется вместо стандартного Djoser current_user сериализатора.
    Сериализует данные авторизованного пользователя в его профиле.
    """
    represent_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        read_only_fields = ['email']
        fields = (
            'id',
            'email',
            'name',
            'represent_name',
        )

    def get_represent_name(self, obj):
        return obj.representation_name()


class PasswordResetSerializer(SendEmailResetSerializer):
    """
    Сериализация почты пользователя для отправки письма при сбросе пароля
    """
    def get_user(self):
        """
        Метод возвращает пользователя которому нужно сбросить пароль.
        Переопределен, чтобы дать возможность сбросить пароль неактивированному юзеру.
        """
        try:
            user = User._default_manager.get(
                **{self.email_field: self.data.get(self.email_field, "")},
            )
            if user.has_usable_password():
                return user
        except User.DoesNotExist:
            pass
        if (
                djoser_settings.PASSWORD_RESET_SHOW_EMAIL_NOT_FOUND
                or djoser_settings.USERNAME_RESET_SHOW_EMAIL_NOT_FOUND
        ):
            self.fail("email_not_found")


class MyTokenObtainSerializer(TokenObtainSerializer):
    """
    Сериализатор логина и пароля пользователя.
    Выводит сообщение об ошибке при авторизации в следующем порядке:
        1. Пользователя с указанным email не существует;
        2. Пользователь ввел неверный пароль;
        3. Учетная запись пользователя не активна.
    После активации аккаунта пользователь сразу авторизован, поэтому прежде чем отправить ссылку
    активации нужно убедиться, что он пытается залогиниться с верным паролем.
    """

    default_error_messages = {
        'no_account': 'Не найдено учетной записи с указанной эл. почтой',
        'invalid_password': 'Неверный пароль',
        'no_active_account': 'Учетная запись с указанными данными не активна',
    }

    def validate(self, attrs):
        authenticate_kwargs = {
            self.username_field: attrs[self.username_field],
            "password": attrs["password"],
        }
        try:
            authenticate_kwargs["request"] = self.context["request"]
        except KeyError:
            pass

        user_exists = User.objects.filter(email=authenticate_kwargs['email']).exists()

        if not user_exists:
            raise exceptions.AuthenticationFailed(
                self.error_messages["no_account"],
                "no_account",
            )

        self.user = authenticate(**authenticate_kwargs)

        if not self.user:
            raise exceptions.AuthenticationFailed(
                self.error_messages["invalid_password"],
                "invalid_password",
            )

        if not api_settings.USER_AUTHENTICATION_RULE(self.user):
            raise exceptions.AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )

        return {}


class MyTokenObtainPairSerializer(TokenObtainPairSerializer, MyTokenObtainSerializer):
    """
    Возвращает токены, если пользователь успешно аутентифицирован
    """
    pass
