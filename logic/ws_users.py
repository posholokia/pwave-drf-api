from typing import Optional

from workspaces.exeptions import InvalidAction
from django.contrib.auth import get_user_model

from workspaces.models import WorkSpace

User = get_user_model()


class WorkSpaceUserHandler:
    def __init__(self, workspace: WorkSpace,
                 email: Optional[str] = None,
                 user: Optional[User] = None):
        self.workspace = workspace
        self.email = email
        self.user = user
        self.errors = {}

    def invite(self):
        self.user = self.get_or_create_user()
        self.checking_possibility_invitation()
        self.add_user_in_workspace()
        return self.workspace, self.user

    def add_user_in_workspace(self):
        if self.errors:
            raise InvalidAction(
                detail=self.errors['detail'],
                code=self.errors['code']
            )

        self.workspace.invited.add(self.user)

    def checking_possibility_invitation(self):
        if self.user_is_added_to_workspace():
            self.errors.update({
                'detail': {"email": 'Пользователь уже добавлен в это рабочее пространство'},
                'code': {'already_added'},
            })

        if self.user_is_invited_to_workspace():
            self.errors.update({
                'detail': {"email": 'Пользователь уже приглашен в это рабочее пространство'},
                'code': {'already_invited'},
            })

    def get_or_create_user(self) -> User:
        """При добавлении пользователя в РП находит указанного пользователя или создает нового"""
        try:
            user = User.objects.get(email=self.email)
        except User.DoesNotExist:
            user_data = {'email': self.email, 'password': None, 'is_active': False, }
            user = User.objects.create_user(**user_data)

        return user

    def user_is_added_to_workspace(self) -> bool:
        if (self.user.id, ) in self.workspace.users.all().values_list('id'):
            return True

        return False

    def user_is_invited_to_workspace(self) -> bool:
        if (self.user.id, ) in self.workspace.invited.all().values_list('id'):
            return True

        return False


ws_users = WorkSpaceUserHandler
