import string
import random

from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action, api_view

from django.contrib.auth import get_user_model

from django_eventstream import send_event

from taskmanager.serializers import CurrentUserSerializer
from .models import *
from . import serializers, mixins
from .permissions import UserInWorkSpaceUsers, UserIsBoardMember, UserHasAccessTasks, UserHasAccessStickers
from logic.ws_users import ws_users
from logic.indexing import index_recalculation
from sse.decorators import sse_send

User = get_user_model()


class WorkSpaceViewSet(mixins.GetInvitationMixin,
                       mixins.UserNoAuthOrThisUser,
                       mixins.CheckWorkSpaceUsersMixin,
                       viewsets.ModelViewSet):
    serializer_class = serializers.WorkSpaceSerializer
    queryset = WorkSpace.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.CreateWorkSpaceSerializer
        elif self.action == 'invite_user':
            return serializers.WorkSpaceInviteSerializer
        elif self.action == 'confirm_invite':
            return serializers.InviteUserSerializer
        elif self.action == 'kick_user':
            return serializers.UserIDSerializer
        elif self.action == 'resend_invite':
            return serializers.ResendInviteSerializer

        return self.serializer_class

    def get_permissions(self):
        if self.action == "confirm_invite":
            self.permission_classes = [permissions.AllowAny, ]

        return super().get_permissions()

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        queryset = (queryset
                    .filter(users=user)
                    .select_related('owner')
                    .prefetch_related('users', 'invited', 'board')
                    )
        return queryset.order_by('created_at')  # вывод РП сортируется по дате создания

    def create(self, request, *args, **kwargs):
        """
        Создание рабочего пространства.
        Изменен только ответ Клиенту - вместо созданного обьекта возвращается массив объектов.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)
        queryset = self.get_queryset()
        serialized_data = self.serializer_class(queryset, many=True).data
        return Response(data=serialized_data, status=status.HTTP_201_CREATED)

    @action(methods=['post'], detail=True, url_name='invite_user')
    def invite_user(self, request, *args, **kwargs):
        """
        Представление для приглашения пользователей в РП.
        Если приглашенного пользователя не существует, он будет создан с пустым паролем.
        Пользователь сперва добавляется в список приглашенных: invited.
        Затем отправляется ссылка на почту с приглашением.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        wp = self.get_object()
        email = serializer.validated_data['email']

        ws_handler = ws_users(wp, email=email)
        workspace, user = ws_handler.invite()

        self.get_or_create_invitation(user, workspace)

        return Response(data=self.serializer_class(workspace).data, status=status.HTTP_200_OK)

    @action(['post'], detail=False, url_name='confirm_invite')
    def confirm_invite(self, request, *args, **kwargs):
        """
        Добавление пользователя в РП и удаление из приглашенных.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.user = serializer.invitation.user
        self.workspace = serializer.invitation.workspace

        if not self.check_auth_user(self.user):
            return Response(status=status.HTTP_403_FORBIDDEN)

        # если пользователь уже добавлен в РП, но не закончил регистрацию, нужно вернуть ответ,
        # по которому его направят на установку пароля
        data = serializers.InviteUserSerializer(serializer.invitation).data
        if not self.user.has_usable_password() and self.user_is_added_to_workspace():
            return Response(data=data, status=status.HTTP_200_OK)

        self.workspace.invited.remove(self.user)
        self.workspace.users.add(self.user)

        if self.user.has_usable_password():
            serializer.invitation.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(data=data, status=status.HTTP_200_OK)

    @action(['post'], detail=True, url_name='kick_user')
    def kick_user(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.data['user_id']

        self.workspace = WorkSpace.objects.get(pk=kwargs['pk'])

        if user_id == self.workspace.owner_id:
            return Response(data={'detail': 'Нельзя удалить владельца РП'},
                            status=status.HTTP_400_BAD_REQUEST)

        self.kick_from_workspace(user_id)

        workspace_data = self.serializer_class(self.workspace).data
        return Response(data=workspace_data, status=status.HTTP_200_OK)

    @action(['post'], detail=True, url_name='resend_invite')
    def resend_invite(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user
        workspace = serializer.workspace

        self.get_or_create_invitation(user, workspace)

        return Response(status=status.HTTP_204_NO_CONTENT)

    def kick_from_workspace(self, user_id):
        self.workspace.users.remove(user_id)
        self.workspace.invited.remove(user_id)
        InvitedUsers.objects.filter(user_id=user_id).delete()

    def get_object(self):
        obj = super().get_object()
        setattr(self, 'workspace', obj)
        return obj


class UserList(generics.ListAPIView):
    """
    Вывод списка всех пользователей при поиске по имени и почте.
    """
    serializer_class = serializers.UserListSerializer
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        filter_email = self.request.query_params.get('users')

        if filter_email and len(filter_email) > 2:
            queryset = (queryset
                        .filter(email__istartswith=filter_email, is_active=True)
                        .exclude(pk=self.request.user.id)
                        )

            return queryset
        return None


class TestSSEMessage(generics.CreateAPIView):
    """Для тестов Server Events. Отправляет случайную строку"""
    serializer_class = None
    queryset = None

    def post(self, request, *args, **kwargs):
        message = ''.join(random.choice(string.ascii_letters) for _ in range(10))
        send_event('test', 'test_message', {'message': message})
        return Response(status=status.HTTP_204_NO_CONTENT)


class TestSSEUser(generics.CreateAPIView):
    """Для тестов Server Events. Отправляет текущего юзера"""
    serializer_class = CurrentUserSerializer
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        user = self.serializer_class(user).data
        send_event('test', 'test_user', {'user': user})
        return Response(status=status.HTTP_204_NO_CONTENT)


class BoardViewSet(viewsets.ModelViewSet):
    """Представление досок"""
    serializer_class = serializers.BoardSerializer
    queryset = Board.objects.all()
    permission_classes = [permissions.IsAuthenticated, UserInWorkSpaceUsers]

    def get_queryset(self):
        queryset = super().get_queryset()
        workspace = self.kwargs.get('workspace_id')
        queryset = queryset.filter(work_space_id=workspace)

        if self.action == 'retrieve':
            queryset = (queryset
                        .prefetch_related('work_space__users')
                        .prefetch_related('members')
                        .prefetch_related('column_board')
                        .prefetch_related('column_board__task')
                        .prefetch_related('column_board__task__responsible')
                        .prefetch_related('column_board__task__sticker')
                        )

        return queryset.order_by('id')

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.CreateBoardSerializer

        return super().get_serializer_class()

    @sse_send
    def create(self, request, *args, **kwargs):
        """ Создание доски с ограничением в 10 шт"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        workspace = self.kwargs.get('workspace_id')
        if Board.objects.filter(work_space_id=workspace).count() < 10:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                data=self.serializer_class(self.get_queryset(), many=True).data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        else:
            return Response(data={'detail': 'Возможно создать не более 10 Досок'}, status=status.HTTP_400_BAD_REQUEST)

    @sse_send
    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        return Response(
            data=self.serializer_class(self.get_queryset(), many=True).data,
        )

    @sse_send
    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response(
            data=self.serializer_class(self.get_queryset(), many=True).data,
        )


class BoardCreateWithoutWorkSpace(generics.CreateAPIView):
    """Создание доски вне РП"""
    serializer_class = serializers.CreateBoardNoWorkSpaceSerializer
    queryset = Board.objects.all()
    permission_classes = [permissions.IsAuthenticated]


class ColumnViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ColumnSerializer
    queryset = Column.objects.all()
    permission_classes = [permissions.IsAuthenticated, UserIsBoardMember]

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.CreateColumnSerializer

        return super().get_serializer_class()

    @sse_send
    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        return Response(
            data=self.serializer_class(self.get_queryset(), many=True).data,
            status=status.HTTP_201_CREATED,
        )

    @sse_send
    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        return Response(
            data=self.serializer_class(self.get_queryset(), many=True).data,
        )

    def get_queryset(self):
        """Колонки отфилрованы по доске"""
        queryset = super().get_queryset()
        board_id = self.kwargs.get('board_id', None)
        queryset = queryset.filter(board_id=board_id)
        return queryset.order_by('index')

    @sse_send
    def destroy(self, request, *args, **kwargs):
        """
        При удалении колонки перезаписывает порядковые номера оставшихся колонок
        """
        instance = self.get_object()
        index_recalculation().delete_shift_index(instance)
        self.perform_destroy(instance)
        return Response(
            data=self.serializer_class(self.get_queryset(), many=True).data,
        )


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.TaskSerializer
    queryset = Task.objects.all()
    permission_classes = [permissions.IsAuthenticated, UserHasAccessTasks]

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.TaskCreateSerializer

        return super().get_serializer_class()

    def get_queryset(self):
        """Задачи фильтруются по колонкам"""
        queryset = super().get_queryset()
        column_id = self.kwargs.get('column_id', None)
        queryset = (queryset
                    .filter(column_id=column_id)
                    .select_related('column')
                    .select_related('column__board')
                    )
        setattr(self, 'queryset', queryset)
        return queryset.order_by('index')

    @sse_send
    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        return Response(
            data=self.serializer_class(self.get_queryset(), many=True).data,
            status=status.HTTP_201_CREATED,
        )

    @sse_send
    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        return Response(
            data=self.serializer_class(self.get_queryset(), many=True).data,
        )
    @sse_send
    def destroy(self, request, *args, **kwargs):
        """
        При удалении задачи перезаписывает порядковые номера оставшихся задач
        """
        instance = self.get_object()
        index_recalculation().delete_shift_index(instance)
        self.perform_destroy(instance)
        return Response(
            data=self.serializer_class(self.get_queryset(), many=True).data,
        )


@api_view(['POST'])
def index_columns(request):
    boards = Board.objects.all()
    for board in boards:
        columns = Column.objects.filter(board=board).order_by('index')
        c_index = 0
        for column in columns:
            tasks = Task.objects.filter(column=column).order_by('index')
            t_index = 0
            for task in tasks:
                task.index = t_index
                task.save()
                t_index += 1

            column.index = c_index
            column.save()
            c_index += 1

    return Response(status=status.HTTP_200_OK)


class StickerViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.StickerCreateSerializer
    queryset = Sticker.objects.all()
    permission_classes = [permissions.IsAuthenticated, UserHasAccessStickers, ]

    def get_queryset(self):
        """Задачи фильтруются по колонкам"""
        queryset = super().get_queryset()
        task_id = self.kwargs.get('task_id', None)
        queryset = queryset.filter(task_id=task_id)
        return queryset

    @sse_send
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @sse_send
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

# @api_view(['POST'])
# def return_ws(request):
#     workspaces = WorkSpace.objects.all()
#     for ws in workspaces:
#         if ws.owner not in ws.users.all():
#             ws.users.add(ws.owner)
#
#     return Response(status=status.HTTP_200_OK)
