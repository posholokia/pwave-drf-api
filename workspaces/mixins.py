from typing import Optional, Union

from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.contrib.auth.models import AnonymousUser
from django.db import transaction
from django.db.models import F, Q

from rest_framework.exceptions import ValidationError

from taskmanager.email import InviteUserEmail
from .models import WorkSpace, InvitedUsers, Board, Column, Task

User = get_user_model()


class GetInvitedMixin:
    def get_invitation(self, **key) -> None:
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
    def get_workspace(self) -> WorkSpace:
        try:
            pk = self.context.get('view').kwargs.get('pk')
            workspace = (
                WorkSpace.objects
                # .prefetch_related('users', 'invited', 'board', )
                .get(pk=pk)
            )
            return workspace

        except WorkSpace.DoesNotExist:
            raise ValidationError(
                {"detail": 'Такого РП не существует'},
            )


class CheckWorkSpaceUsersMixin:
    """Проверка, что пользователь является участником РП"""
    def user_is_added_to_workspace(self) -> bool:
        if (self.user.id, ) in self.workspace.users.all().values_list('id'):
            return True

        return False


class CheckWorkSpaceInvitedMixin:
    """Проверка, что пользователь приглашен в РП"""
    def user_is_invited_to_workspace(self) -> bool:
        if (self.user.id, ) in self.workspace.invited.all().values_list('id'):
            return True

        return False


class GetInvitationMixin:
    def get_or_create_invitation(self, user: User, workspace: WorkSpace) -> InvitedUsers:
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
    def get_or_create_user(self, email: str) -> User:
        """При добавлении пользователя в РП находит указанного пользователя или создает нового"""
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user_data = {'email': email, 'password': None, 'is_active': False, }
            user = User.objects.create_user(**user_data)
        return user


class UserNoAuthOrThisUser:
    def check_auth_user(self, user: User) -> bool:
        """
        Проверка, если пользователь авторизован, то это нужный пользователь.
        (Например, что по приглашению перешел тот же пользователь, которого пригласили)
        """
        if any([isinstance(self.request.user, AnonymousUser), self.request.user == user]):
            return True

        return False


class DefaultWorkSpaceMixin:
    """Создание РП по умолчанию"""
    def create_default_workspace(self, user: User, create_for_board: Optional[bool] = None) -> WorkSpace:
        workspace = WorkSpace.objects.create(owner=user, name='Рабочее пространство 1')
        workspace.users.add(user)

        if not create_for_board:
            Board.objects.create(name='Доска 1', work_space=workspace)

        return workspace


class ColumnValidateMixin:
    def column_validate(self, new_index: int, new_col: Column):
        valid_columns = self.instance.column.board.column_board.all().values_list('id')
        if (new_col.id, ) not in valid_columns:
            raise ValidationError(
                {"column": 'Задачи можно перемещать только между колонками внутри доски'},
                'invalid_column'
            )

        # меняем номер колонки, чтобы при валидации индекса задачи
        # не было ошибок в крайних случаях (0 или максимальное значение индекса)
        self.instance.column = new_col
        self.instance.save()

        if new_index is not None:
            self.index_validate(new_index, new_col)


class IndexValidateMixin:
    def index_validate(self, new_index: int, new_col: Optional[Column] = None):
        """
        Валидация нового индекса обьекта. Проверяет, что индекс не выходит за
        пределы количества обьектов
        """
        if new_col is not None:
            # условие применяется для задач, если задачу перемещают между колонками,
            # список обьектов нужно получить из другой колонки
            objects = new_col.task.all().order_by('index')
        else:
            objects = self.context['view'].get_queryset()

        if new_index > len(objects) or new_index < 0:
            raise ValidationError(
                {"index": f'Порядковый номер должен соответсвовать количеству обьектов: '
                          f'0 <= index <= {len(objects) - 1}'},
                'invalid_index'
            )
        return objects
