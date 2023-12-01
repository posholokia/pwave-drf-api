from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.contrib.auth.models import AnonymousUser

from rest_framework.exceptions import ValidationError

from taskmanager.email import InviteUserEmail
from .models import WorkSpace, InvitedUsers

User = get_user_model()


class GetInvitedMixin:
    def get_invitation(self, **key):
        self.invitation = (
            InvitedUsers.objects.filter(**key)
            .select_related('user', 'workspace')
            .first()
        )
        if self.invitation is None:
            raise ValidationError(
                {"token": self.default_error_messages['invalid_token']},
                'invalid_token'
            )


class GetWorkSpaceMixin:
    def get_workspace(self):
        try:
            pk = self.context.get('view').kwargs.get('pk')
            workspace = (
                WorkSpace.objects
                .prefetch_related('users', 'invited', 'board', )
                .get(pk=pk)
            )
            return workspace

        except WorkSpace.DoesNotExist:
            raise ValidationError(
                {"detail": 'Такого РП не существует'},
            )


class CheckWorkSpaceUsersMixin:
    def user_is_added_to_workspace(self):
        if self.user in self.workspace.users.all():
            return True

        return False


class CheckWorkSpaceInvitedMixin:
    def user_is_invited_to_workspace(self):
        if self.user in self.workspace.invited.all():
            return True

        return False


class GetInvitationMixin:
    def get_or_create_invitation(self, user, workspace):
        try:
            invitation = InvitedUsers.objects.get(user=user, workspace=workspace)
        except InvitedUsers.DoesNotExist:
            invitation = InvitedUsers.objects.create(
                user=user,
                token=get_random_string(length=32),
                workspace=workspace,
            )

        context = {'invitation': invitation, }
        to = [invitation.user.email]
        InviteUserEmail(self.request, context).send(to)

        return invitation


class GetOrCreateUserMixin:
    def get_or_create_user(self, email):
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user_data = {'email': email, 'password': None, 'is_active': False, }
            user = User.objects.create_user(**user_data)

        return user


class UserNoAuthOrThisUser:
    def check_auth_user(self, user):
        if any([isinstance(self.request.user, AnonymousUser), self.request.user == user]):
            return True

        return False