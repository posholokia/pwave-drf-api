import string
import random

from django.db.models import Prefetch
from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from rest_framework.mixins import (CreateModelMixin,
                                   UpdateModelMixin,
                                   DestroyModelMixin,
                                   ListModelMixin,
                                   RetrieveModelMixin)

from django.contrib.auth import get_user_model

from django_eventstream import send_event

from .models import *
from . import serializers, mixins
from .permissions import *
from taskmanager.serializers import CurrentUserSerializer

from logic.ws_users import ws_users
from logic.indexing import index_recalculation
from notification.create_notify.decorators import send_notify
from sse.decorators import sse_create

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
    @send_notify
    def invite_user(self, request, *args, **kwargs):
        """
        Представление для приглашения пользователей в РП.
        Если приглашенного пользователя не существует, он будет создан с пустым паролем.
        Пользователь сперва добавляется в список приглашенных: invited.
        Затем отправляется ссылка на почту с приглашением.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ws = self.get_object()
        email = serializer.validated_data['email']

        ws_handler = ws_users(ws, email=email)
        workspace = ws_handler.invite(request)

        return Response(data=self.serializer_class(workspace).data, status=status.HTTP_200_OK)

    @action(['post'], detail=False, url_name='confirm_invite')
    def confirm_invite(self, request, *args, **kwargs):
        """
        Добавление пользователя в РП и удаление из приглашенных.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.invitation.user
        workspace = serializer.invitation.workspace

        # если по ссылке перешел другой залогиненый пользователь
        # необходимо вернуть 403 ответ, чтобы пользователь перелогинился
        if not self.check_auth_user(user):
            return Response(status=status.HTTP_403_FORBIDDEN)

        ws_handler = ws_users(workspace, user=user)
        response = ws_handler.confirm_invite(serializer.invitation)
        return response

    @action(['post'], detail=True, url_name='kick_user')
    @send_notify
    def kick_user(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # если РП не существует, запрос не будет выполнен на уровне permissions
        # можно безболезненно использовать get()
        workspace = self.get_object()

        ws_handler = ws_users(workspace, user=serializer.user)
        ws_handler.kick_user()

        workspace_data = self.serializer_class(workspace).data
        return Response(data=workspace_data, status=status.HTTP_200_OK)

    @action(['post'], detail=True, url_name='resend_invite')
    def resend_invite(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ws_handler = ws_users(serializer.workspace, user=serializer.user)
        ws_handler.resend_invite(request)

        return Response(status=status.HTTP_204_NO_CONTENT)


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


class BoardViewSet(viewsets.ModelViewSet):
    """Представление досок"""
    serializer_class = serializers.BoardSerializer
    queryset = Board.objects.all()
    permission_classes = [permissions.IsAuthenticated, UserInWorkSpaceUsers]

    def get_queryset(self):
        queryset = super().get_queryset()
        workspace = self.kwargs.get('workspace_id')
        queryset = queryset.filter(work_space_id=workspace)

        if self.action == 'retrieve' or self.action == 'list':
            queryset = (queryset
                        .prefetch_related('members')
                        .prefetch_related('column_board')
                        .prefetch_related('column_board__task')
                        .prefetch_related('column_board__task__responsible')
                        .prefetch_related(Prefetch('column_board__task__sticker',
                                                   queryset=Sticker.objects.order_by('id')))
                        )

        return queryset.order_by('id')

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.CreateBoardSerializer

        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        """ Создание доски с ограничением в 10 шт"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        workspace = self.kwargs.get('workspace_id')

        if Board.objects.filter(work_space_id=workspace).count() < 10:
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail': 'Возможно создать не более 10 Досок'}, status=status.HTTP_400_BAD_REQUEST)

    @sse_create(event_type=['board', ])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class BoardCreateWithoutWorkSpace(generics.CreateAPIView):
    """Создание доски вне РП"""
    serializer_class = serializers.CreateBoardNoWorkSpaceSerializer
    queryset = Board.objects.all()
    permission_classes = [permissions.IsAuthenticated]


class ColumnViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ColumnSerializer
    queryset = Column.objects.all()
    permission_classes = [permissions.IsAuthenticated, UserIsBoardMember]

    # def get_queryset(self):
    #     """Колонки отфилрованы по доске"""
    #     queryset = super().get_queryset()
    #     board_id = self.kwargs.get('board_id', None)
    #     queryset = (queryset
    #                 .filter(board_id=board_id)
    #                 .prefetch_related('task')
    #                 .prefetch_related('task__responsible')
    #                 .prefetch_related('task__sticker')
    #                 )
    #
    #     return queryset.order_by('index')

    def get_queryset(self):
        """Колонки отфилрованы по доске"""
        queryset = super().get_queryset()
        board_id = self.kwargs.get('board_id', None)
        queryset = queryset.filter(board_id=board_id)
        if (self.action == 'partial_update'
                or self.action == 'update'):
            return queryset.order_by('index')

        queryset = (queryset
                    .prefetch_related('task')
                    .prefetch_related('task__responsible')
                    .prefetch_related('task__sticker')
                    )

        return queryset.order_by('index')

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.CreateColumnSerializer

        return super().get_serializer_class()

    @sse_create(event_type=['board', ])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @sse_create(event_type=['board', ])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @sse_create(event_type=['board', ])
    def destroy(self, request, *args, **kwargs):
        """
        При удалении колонки перезаписывает порядковые номера оставшихся колонок
        """
        instance = self.get_object()
        index_recalculation().delete_shift_index(instance)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RetrieveTask(RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = serializers.TaskSerializer
    queryset = Task.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        task_id = self.kwargs.get('pk', None)
        queryset = queryset.filter(pk=task_id)

        queryset = (queryset
                    .prefetch_related('responsible')
                    .prefetch_related(Prefetch('sticker',
                                               queryset=Sticker.objects.order_by('id')))
                    .prefetch_related(Prefetch('comments',
                                               queryset=Comment.objects.order_by('id')))
                    )
        return queryset


class TaskViewSet(CreateModelMixin,
                  UpdateModelMixin,
                  DestroyModelMixin,
                  ListModelMixin,
                  viewsets.GenericViewSet
                  ):
    serializer_class = serializers.TaskSerializer
    queryset = Task.objects.all()
    permission_classes = [permissions.IsAuthenticated, UserHasAccessTasks]

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.TaskCreateSerializer
        elif self.action == 'list':
            return serializers.TaskListSerializer

        return super().get_serializer_class()

    def get_queryset(self):
        """Задачи фильтруются по колонкам"""
        queryset = super().get_queryset()
        column_id = self.kwargs.get('column_id', None)
        queryset = queryset.filter(column_id=column_id)
        queryset = (queryset
                    .prefetch_related('responsible')
                    .prefetch_related(Prefetch('sticker',
                                               queryset=Sticker.objects.order_by('id')))
                    .prefetch_related(Prefetch('comments',
                                               queryset=Comment.objects.order_by('id')))
                    )

        return queryset.order_by('index')

    @sse_create(event_type=['board', ])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @send_notify
    @sse_create(event_type=['board', 'task', ])
    def update(self, request, *args, **kwargs):
        # Из метода удалена джанговская инвалидация кэша,
        # иначе связанные объекты выводит в случайной сортировке.
        # Инвалидацию кэша осуществляет cacheops.
        # (Также лечится принтом serializer.data перед инвалидацией кэша)
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @send_notify
    @sse_create(event_type=['board', ])
    def destroy(self, request, *args, **kwargs):
        """
        При удалении задачи перезаписывает порядковые номера оставшихся задач
        """
        instance = self.get_object()
        index_recalculation().delete_shift_index(instance)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommentViewSet(ListModelMixin,
                     CreateModelMixin,
                     DestroyModelMixin,
                     viewsets.GenericViewSet):
    queryset = Comment.objects.all()
    serializer_class = serializers.CommentSerializer
    permission_classes = [permissions.IsAuthenticated, UserHasAccessStickers, ]

    def get_queryset(self):
        """Комменты фильтруются по задачам"""
        queryset = super().get_queryset()
        task_id = self.kwargs.get('task_id', None)
        queryset = queryset.filter(task_id=task_id)
        return queryset

    @sse_create(event_type=['board', 'task', ])
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user == instance.author:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(data={'detail': 'Вы не являетесь автором комментария.'}, status=status.HTTP_403_FORBIDDEN)

    @send_notify
    @sse_create(event_type=['board', 'task', ])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


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
        """Стикеры фильтруются по задачам"""
        queryset = super().get_queryset()
        task_id = self.kwargs.get('task_id', None)
        queryset = queryset.filter(task_id=task_id)
        return queryset

    @sse_create(event_type=['board', 'task', ])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @sse_create(event_type=['board', 'task', ])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @sse_create(event_type=['board', 'task', ])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


# @api_view(['POST'])
# def return_ws(request):
#     workspaces = WorkSpace.objects.all()
#     for ws in workspaces:
#         if ws.owner not in ws.users.all():
#             ws.users.add(ws.owner)
#
#     return Response(status=status.HTTP_200_OK)


class BoardUserList(generics.ListAPIView):
    """
    Вывод списка всех пользователей доски.
    Для назначения ответственных за задачи.
    """
    serializer_class = serializers.BoardUserListSerializer
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        ws_filter = self.request.query_params.get('workspace')

        if ws_filter:
            queryset = (
                queryset
                .filter(joined_workspaces__id=ws_filter)
            )
            return list(queryset)
        return None
