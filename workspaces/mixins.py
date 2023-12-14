from typing import Optional

from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.contrib.auth.models import AnonymousUser
from django.db import transaction

from rest_framework.exceptions import ValidationError

from taskmanager.email import InviteUserEmail
from .models import WorkSpace, InvitedUsers, Board, Column, Task

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
    def get_or_create_invitation(self, user: User, workspace: WorkSpace):
        try:
            invitation = InvitedUsers.objects.get(user=user, workspace=workspace)
        except InvitedUsers.DoesNotExist:
            invitation = InvitedUsers.objects.create(
                user=user,
                token=get_random_string(length=32),
                workspace=workspace,
            )

        context = {
            'invitation': invitation,
            'workspace': workspace.name,
        }
        to = [invitation.user.email]
        InviteUserEmail(self.request, context).send(to)

        return invitation


class GetOrCreateUserMixin:
    def get_or_create_user(self, email: str):
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user_data = {'email': email, 'password': None, 'is_active': False, }
            user = User.objects.create_user(**user_data)

        return user


class UserNoAuthOrThisUser:
    def check_auth_user(self, user: User):
        if any([isinstance(self.request.user, AnonymousUser), self.request.user == user]):
            return True

        return False


class DefaultWorkSpaceMixin:
    def create_default_workspace(self, user: User, create_for_board: Optional[bool] = None):
        workspace = WorkSpace.objects.create(owner=user, name='Рабочее пространство 1')
        workspace.users.add(user)

        if not create_for_board:
            Board.objects.create(name='Доска 1', work_space=workspace)

        return workspace


class IndexValidateMixin:
    def index_validate(self, new_index, new_col=None):
        if new_col is not None:
            self.objects = Task.objects.filter(column=new_col).order_by('index')
        else:
            self.objects = self.context['view'].get_queryset()

        if new_index >= len(self.objects) or new_index < 0:
            raise ValidationError(
                {"index": f'Порядковый номер должен соответсвовать количеству обьектов: '
                          f'0 <= index <= {len(self.objects) - 1}'},
                'invalid_index'
            )


class ShiftIndexMixin:
    def shift_indexes(self, instance, new_index):
        if new_index >= instance.index:
            instance = self.left_shift(instance, new_index)
        elif new_index <= instance.index:
            instance = self.right_shift(instance, new_index)
        return instance

    def insert_object(self, instance, new_index, new_col):
        instance.column = new_col
        instance.index = None
        return self.right_shift(instance, new_index)

    def left_shift(self, instance, new_index):
        slice_objects = self.objects[instance.index: new_index + 1]

        with transaction.atomic():
            for obj in slice_objects:
                obj.index -= 1
            instance.index = new_index
            instance.__class__.objects.bulk_update(slice_objects, ['index'])
            return instance

    def right_shift(self, instance, new_index):
        right_border = instance.index + 1 if instance.index is not None else None
        slice_objects = self.objects[new_index: right_border]

        with transaction.atomic():
            for obj in slice_objects:
                obj.index += 1
            instance.index = new_index
            instance.__class__.objects.bulk_update(slice_objects, ['index'])
            return instance


class ShiftIndexAfterDeleteMixin:
    def delete_shift_index(self, instance):
        list_objects = self.get_queryset()[instance.index + 1:]
        with transaction.atomic():
            for obj in list_objects:
                obj.index -= 1

            instance.__class__.objects.bulk_update(list_objects, ['index'])
