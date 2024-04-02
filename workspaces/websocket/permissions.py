from djangochannelsrestframework.permissions import BasePermission
from typing import Dict, Any
from channels.consumer import AsyncConsumer
from django.contrib.auth import get_user_model

from workspaces.models import Task

User = get_user_model()


class IsAuthenticated(BasePermission):
    async def has_permission(
            self, scope: Dict[str, Any], consumer: AsyncConsumer, action: str, **kwargs
    ) -> bool:
        user = scope.get("user")
        if type(user) is User:
            return user.pk and user.is_authenticated

        return False

    async def can_connect(
            self, scope: Dict[str, Any],
            consumer: AsyncConsumer,
            message=None
    ) -> bool:
        user = scope.get("user")
        if type(user) is User:
            return user.pk and user.is_authenticated
        return False


class ThisTaskInUserWorkspace(BasePermission):
    async def has_permission(
            self, scope: Dict[str, Any], consumer: AsyncConsumer, action: str, **kwargs
    ) -> bool:
        user = scope.get("user")
        task_id = kwargs.get('pk')

        if task_id is not int:
            return True
        elif await Task.objects.filter(
                column__board__workspace__users__in=[user.pk],
                pk=task_id
        ).aexists():
            return True

        return False

class UserInWorkSpaceUsers(BasePermission):
    """Настройка прав для досок, пользователь является участником РП"""
    async def has_permission(
        self, scope: Dict[str, Any], consumer: AsyncConsumer, action: str, **kwargs
    ) -> bool:
        user = scope.get("user")
        workspace_id = kwargs.get('workspace')

        if workspace_id is not int:
            return True
        elif await user.joined_workspaces.filter(id=workspace_id).aexists():
            return True

        return False
