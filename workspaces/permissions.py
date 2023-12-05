from rest_framework.permissions import BasePermission, SAFE_METHODS

from workspaces.models import Board


class UserIsMember(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        board_id = request.data.get('board', None)
        board = Board.objects.filter(pk=board_id).first()

        if board and request.user in board.members.all():
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if (request.method in SAFE_METHODS) or (request.user in obj.board.members.all()):
            return True

        return False
