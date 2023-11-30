from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

from rest_framework.exceptions import ValidationError

from taskmanager.email import InviteUserEmail
from .models import WorkSpace, InvitedUsers
from .tasks import delete_invited

User = get_user_model()


class GetInvitedMixin:
    def get_invitation(self, **key):
        self.invited_user = (
            InvitedUsers.objects.filter(**key)
            .select_related('user', 'workspace')
            .first()
        )
        if self.invited_user is None:
            raise ValidationError(
                {"token": self.default_error_messages['invalid_token']},
                'invalid_token'
            )


# class GetUserMixin:
#     def get_user_object(self, **key):
#         try:
#             self.user = User.objects.get(**key)
#         except User.DoesNotExist:
#             raise ValidationError(
#                 {"user": self.default_error_messages['invalid_user']},
#                 'invalid_user'
#             )


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
        delete_invited.apply_async((invitation.id,), countdown=24 * 60 * 60)

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
