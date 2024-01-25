from typing import Optional

from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

from rest_framework.response import Response
from rest_framework import status

from logic.email import InviteUserEmail
from workspaces.models import WorkSpace, InvitedUsers, Task
from workspaces.serializers import InviteUserSerializer
from workspaces.exeptions import InvalidAction

User = get_user_model()


class WorkSpaceUserHandler:
    def __init__(self,
                 workspace: WorkSpace,
                 email: Optional[str] = None,
                 user: Optional[User] = None):
        self.workspace = workspace
        self.email = email
        self.user = user
        self.errors = {}

    def invite(self, request):
        assert (self.email is None or self.email is not str), \
            ('Неверный email. При инициализации класса email не был '
             'передан или имеет недопустимый формат')
        self.user = self._get_or_create_user()
        self._checking_possibility_invitation()
        self._invite_user_in_workspace()
        self._get_or_create_invitation(request)
        return self.workspace

    def confirm_invite(self, invitation):
        assert (self.user is None or self.user is not User), \
            ('Неверный user. При инициализации класса user не был '
             'передан или не является обьектом класса User')

        # если пользователь уже добавлен в РП, но не закончил регистрацию,
        # нужно вернуть ответ по которому его направят на установку пароля
        data = InviteUserSerializer(invitation).data
        if self._user_dont_finish_reg() and self._user_is_added_to_workspace():
            return Response(data=data, status=status.HTTP_200_OK)

        self._invte_to_ws()
        if self._user_dont_finish_reg():
            invitation.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(data=data, status=status.HTTP_200_OK)

    def kick_user(self):
        assert (self.user is None or self.user is not User), \
            ('Неверный user. При инициализации класса user не был '
             'передан или не является обьектом класса User')
        self._can_kick_user()
        self._kick()

    def resend_invite(self, request):
        assert (self.user is None or self.user is not User), \
            ('Неверный user. При инициализации класса user не был '
             'передан или не является обьектом класса User')
        self._get_or_create_invitation(request)

    def _kick(self):
        if self.errors:
            raise InvalidAction(
                detail=self.errors['detail'],
                code=self.errors['code']
            )
        self.workspace.users.remove(self.user)
        self.workspace.invited.remove(self.user)

        # удаление пользователя из ответсвенных за задачи в РП
        tasks = Task.objects.filter(
            column__board__work_space_id=self.workspace.id
        )
        for task in tasks:
            task.responsible.remove(self.user)

        InvitedUsers.objects.filter(user=self.user).delete()

    def _can_kick_user(self):
        if self.user == self.workspace.owner:
            self.errors.update({
                'detail': {"detail": 'Нельзя удалить владельца РП'},
                'code': 'delete_owner',
            })

    def _get_or_create_invitation(self, request) -> InvitedUsers:
        try:
            invitation = InvitedUsers.objects.get(
                user=self.user,
                workspace=self.workspace
            )
        except InvitedUsers.DoesNotExist:
            invitation = InvitedUsers.objects.create(
                user=self.user,
                token=get_random_string(length=32),
                workspace=self.workspace,
            )

        context = {
            'invitation': invitation,
            'workspace': self.workspace.name,
        }
        to = [invitation.user.email]
        InviteUserEmail(request, context).send(to)

        return invitation

    def _invte_to_ws(self):
        self.workspace.invited.remove(self.user)
        self.workspace.users.add(self.user)

    def _user_dont_finish_reg(self):
        if self.user.has_usable_password():
            return True
        else:
            return False

    def _invite_user_in_workspace(self):
        if self.errors:
            raise InvalidAction(
                detail=self.errors['detail'],
                code=self.errors['code']
            )

        self.workspace.invited.add(self.user)

    def _checking_possibility_invitation(self):
        if self._user_is_added_to_workspace():
            self.errors.update({
                'detail': {"email": 'Пользователь уже добавлен '
                                    'в это рабочее пространство'},
                'code': 'already_added',
            })

        if self._user_is_invited_to_workspace():
            self.errors.update({
                'detail': {"email": 'Пользователь уже приглашен '
                                    'в это рабочее пространство'},
                'code': 'already_invited',
            })

    def _get_or_create_user(self) -> User:
        """При добавлении пользователя в РП находит указанного
         пользователя или создает нового без пароля и неактивированного"""
        try:
            user = User.objects.get(email=self.email)
        except User.DoesNotExist:
            user_data = {'email': self.email, 'password': None, 'is_active': False, }
            user = User.objects.create_user(**user_data)

        return user

    def _user_is_added_to_workspace(self) -> bool:
        """Проверка, что пользователь добавлен в РП"""
        if (self.user.id, ) in self.workspace.users.all().values_list('id'):
            return True

        return False

    def _user_is_invited_to_workspace(self) -> bool:
        """Проверка, что пользователь приглашен в РП"""
        if (self.user.id, ) in self.workspace.invited.all().values_list('id'):
            return True

        return False


ws_users = WorkSpaceUserHandler
