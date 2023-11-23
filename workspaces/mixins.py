from .models import WorkSpace, Board, InvitedUsers
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

User = get_user_model()


class GetInvitedMixin:
    def get_invited_user(self, **key):
        try:
            self.invited_user = InvitedUsers.objects.get(**key)
        except InvitedUsers.DoesNotExist:
            raise ValidationError(
                {"token": self.default_error_messages['invalid_token']},
                'invalid_token'
            )


class GetUserMixin:
    def get_user_object(self, **key):
        try:
            self.user = User.objects.get(**key)
        except User.DoesNotExist:
            raise ValidationError(
                {"user": self.default_error_messages['invalid_user']},
                'invalid_user'
            )


class GetWorkSpaceMixin:
    def get_workspace(self):
        try:
            pk = self.context.get('view').kwargs.get('pk')
            self.workspace = WorkSpace.objects.get(pk=pk)
        except WorkSpace.DoesNotExist:
            raise ValidationError(
                {"detail": 'Такого РП не существует'},
            )
        return self.workspace


class CheckWorkSpaceUsersMixin:
    def is_user_added(self):
        if self.workspace.users.filter(pk=self.user.id).exists():
            return True

        return False


class CheckWorkSpaceInvitedMixin:
    def is_user_invited(self):
        if self.workspace.invited.filter(pk=self.user.id).exists():
            return True

        return False


class GetInvitedUsersMixin:
    def get_or_create_invited_users(self, user, workspace):
        try:
            invite_user = InvitedUsers.objects.get(user=user, workspace=workspace)
        except InvitedUsers.DoesNotExist:
            invite_user = InvitedUsers.objects.create(
                user=user,
                token=get_random_string(length=32),
                workspace=workspace,
            )
        return invite_user


class GetCreateUserMixin:
    def get_or_create_user(self, email):
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user_data = {'email': email, 'password': None, 'is_active': False, }
            user = User.objects.create_user(**user_data)

        return user
