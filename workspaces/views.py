import string
import random

from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action

from django.contrib.auth import get_user_model

from django_eventstream import send_event

from drf_spectacular.utils import extend_schema, extend_schema_view

from taskmanager.serializers import CurrentUserSerializer
from .models import WorkSpace, Board
from . import serializers, mixins
from .serializers import InviteUserSerializer

User = get_user_model()


@extend_schema_view(list=extend_schema(description='Список всех Рабочих пространств '
                                                   'авторизованного пользователя'),
                    create=extend_schema(description='Создать Рабочее пространство'),
                    retrieve=extend_schema(description='Информация о конктретном рабочем пространстве'),
                    update=extend_schema(description='Обновить все данные РП (на данный момент только имя)'),
                    partial_update=extend_schema(
                        description='Частично обновить данные РП (на данный момент только имя)'),
                    destroy=extend_schema(description='Удалить РП'),
                    )
class WorkSpaceViewSet(mixins.CheckWorkSpaceUsersMixin,
                       mixins.CheckWorkSpaceInvitedMixin,
                       mixins.GetInvitedUsersMixin,
                       mixins.GetCreateUserMixin,
                       viewsets.ModelViewSet):
    serializer_class = serializers.WorkSpaceSerializer
    queryset = WorkSpace.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    ordering_fields = 'created_at'  # вывод РП сортируется по дате создания

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
        if self.action == "confirm_invite_new_user":
            self.permission_classes = [permissions.AllowAny]
        elif self.action == "confirm_invite":
            self.permission_classes = [permissions.AllowAny]

        return super().get_permissions()

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        queryset = queryset.filter(users=user)
        return queryset

    @extend_schema(description='Пригласить пользователя по email.\n\n'
                               'Пользователи добавляются по одному.'
                               'Если пользователя не существует, он будет создан.')
    @action(methods=['post'], detail=True)
    def invite_user(self, request, *args, **kwargs):
        """
        Представление для приглашения пользователей в РП.
        Если приглашенного пользователя не существует, он будет создан с пустым паролем.
        Пользователь сперва добавляется в список приглашенных: invited.
        Затем отправляется ссылка на почту с приглашением.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_email = request.POST['email']

        self.workspace = serializer.get_workspace()
        self.user = self.get_or_create_user(user_email)

        if self.is_user_added():
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={'email': 'Пользователь уже добавлен в это рабочее пространство'})

        if self.is_user_invited():
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={'email': 'Пользователь уже приглашен в это рабочее пространство'})

        self.workspace.invited.add(self.user)
        self.get_or_create_invited_users(self.user, self.workspace)

        return Response(data=self.serializer_class(self.workspace).data, status=status.HTTP_200_OK)

    @extend_schema(description='Добавить пользователя в РП.\n\n'
                               'Здесь добавляются уже зарегистрированные пользователи.\n\n'
                               'Ссылка на приглашение: auth/invite-new-user/{wuid}/{uid}/{token}')
    @action(['post'], detail=False)
    def confirm_invite(self, request, *args, **kwargs):
        """
        Добавление пользователя в РП и удаление из приглашенных.
        В этом представлении добавляются пользователи, которые были зарегистрирвоаны
        на момент приглашения.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.invited_user.user
        workspace = serializer.invited_user.workspace

        workspace.invited.remove(user)
        workspace.users.add(user)

        data = InviteUserSerializer(serializer.invited_user).data
        if user.has_usable_password():
            serializer.invited_user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(data=data, status=status.HTTP_200_OK)

    @extend_schema(description='Удаление пользователей из РП\n\nУдаление как из участников так и из приглашенных')
    @action(['post'], detail=True)
    def kick_user(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.data['user_id']
        workspace = WorkSpace.objects.get(pk=kwargs['pk'])

        workspace.invited.remove(user_id)
        workspace.users.remove(user_id)

        workspace_data = self.serializer_class(workspace).data,
        return Response(data=workspace_data, status=status.HTTP_200_OK)

    @extend_schema(description='Повторная отправка ссылки с приглашением пользователя.')
    @action(['post'], detail=True)
    def resend_invite(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user
        workspace = serializer.workspace

        self.get_or_create_invited_users(user, workspace)

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(list=extend_schema(
    description='Список всех пользователей для поиска.\n\n'
                'Поиск ведется по почте и имени, начало передается через query '
                'параметр users.\n\n Например: /api/user_list/?users=foobar'
    ), )
class UserList(generics.ListAPIView):
    """
    Вывод списка всех пользователей при поиске по имени и почте.
    """
    serializer_class = serializers.UserListSerializer
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        filter_parameter = self.request.query_params.get('users')
        if filter_parameter and len(filter_parameter) > 2:
            queryset = queryset.filter(email__istartswith=filter_parameter)
            return queryset
        return None


class TestSSEMessage(generics.CreateAPIView):
    """
    Создать SSE - передает случайную строку.
    Слушать /events/
    channel: test
    event_type: test_message
    """
    serializer_class = None
    queryset = None

    def post(self, request, *args, **kwargs):
        message = ''.join(random.choice(string.ascii_letters) for _ in range(10))
        send_event('test', 'test_message', {'message': message})
        return Response(status=status.HTTP_204_NO_CONTENT)


class TestSSEUser(generics.CreateAPIView):
    """
    Создать SSE - передает текущего юзера.
    Слушать /events/
    channel: test
    event_type: test_user
    """
    serializer_class = CurrentUserSerializer
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        user = self.serializer_class(user).data
        send_event('test', 'test_user', {'user': user})
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(list=extend_schema(description='Список всех досок этого пользователя. '
                                                   'Для получения досок конкретного РП нужно передать query параметр'
                                                   '"space_id": /api/board/?space_id=4'),
                    create=extend_schema(description='Создать Доску'),
                    retrieve=extend_schema(description='Информация о конкретной доске'),
                    update=extend_schema(description='Обновить доску'),
                    partial_update=extend_schema(description='Частично обновить доску'),
                    destroy=extend_schema(description='Удалить доску'),
                    )
class BoardViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.BoardSerializer
    queryset = Board.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        queryset = queryset.filter(members=user)
        workspace = self.request.query_params.get('space_id')

        if workspace:
            queryset = queryset.filter(work_space_id=workspace)

        return queryset
