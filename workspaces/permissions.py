from rest_framework.permissions import BasePermission

from workspaces.models import Board


class UserInWorkSpaceUsers(BasePermission):
    def has_permission(self, request, view):
        workspace_id = int(view.kwargs.get('workspace_id', None))
        if (workspace_id, ) in request.user.joined_workspaces.all().values_list('id'):
            return True

        return False


class UserIsBoardMember(BasePermission):
    def has_permission(self, request, view):
        board_id = int(view.kwargs.get('board_id', None))

        try:
            if request.user in Board.objects.get(pk=board_id).work_space.users.all():
                return True
        except Board.DoesNotExist:
            return False

        return False
