from rest_framework import viewsets, permissions, status, generics
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response
from rest_framework.decorators import action

from django.contrib.auth import get_user_model

from drf_spectacular.utils import extend_schema, extend_schema_view

from taskmanager.email import InviteUserEmail
from .models import WorkSpace
from . import serializers

User = get_user_model()


@extend_schema_view(list=extend_schema(description='Список всех Рабочих пространств '
                                                   'авторизованного пользователя'),
                    create=extend_schema(description='Создать Рабочее пространство'),
                    retrieve=extend_schema(description='Информация о конктретном рабочем пространстве'),
                    update=extend_schema(description='Обновить все данные РП (на данный момент только имя)'),
                    partial_update=extend_schema(description='Частично обновить данные РП (на данный момент только имя)'),
                    destroy=extend_schema(description='Удалить РП'),
                    )
class WorkSpaceViewSet(viewsets.ModelViewSet):
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
        elif self.action == 'confirm_invite_new_user':
            return serializers.InviteNewUserSerializer

        return self.serializer_class

    def get_permissions(self):
        if self.action == "confirm_invite_new_user":
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
        workspace = WorkSpace.objects.get(pk=kwargs['pk'])
        invite_user = User.objects.filter(email=user_email).first()

        if workspace.users.filter(email=user_email).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={'email': 'Пользователь уже добавлен в это рабочее пространство'})
        elif workspace.invited.filter(email=user_email).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={'email': 'Пользователь уже приглашен в это рабочее пространство'})

        new_user = False
        if not invite_user:
            user_data = {'email': user_email, 'is_active': False, }
            invite_user = User.objects.create_user(**user_data)
            new_user = True

        workspace.invited.add(invite_user)

        context = {'user': invite_user, 'workspace': workspace, 'new_user': new_user}
        to = [user_email]
        InviteUserEmail(self.request, context).send(to)

        return Response(data=self.serializer_class(workspace).data, status=status.HTTP_200_OK)

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

        workspace = serializer.workspace
        user = request.user
        if user == serializer.user:
            workspace.invited.remove(user)
            workspace.users.add(user)
            return Response(data=self.serializer_class(workspace).data, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={'detail': 'Приглашение недействительно для текущего пользователя'})

    @extend_schema(description='Добавить пользователя в РП.\n\n'
                               'Здесь добавляются не зарегистрированные пользователи, которых создали при '
                               'приглашении.\n\n'
                               'Ссылка на приглашение: u/security/invite-exists-user/{wuid}/{uid}/{token}',
                   )
    @action(['post'], detail=False)
    def confirm_invite_new_user(self, request, *args, **kwargs):
        """
       Добавление пользователя в РП и удаление из приглашенных.
       В этом представлении добавляются пользователи, которых не было на момент пришлашения
       и их создали автоматически.
       """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.user.set_password(serializer.data["new_password"])

        user = serializer.user
        serializer.workspace.invited.remove(user)
        serializer.workspace.users.add(user)

        return Response(data=self.serializer_class(serializer.workspace).data, status=status.HTTP_200_OK)


@extend_schema_view(list=extend_schema(description='Список всех пользователей для поиска.\n\n'
                                                   'Поиск ведется по почте, начало почты передается через query '
                                                   'параметр users.\n\n\ Например: /api/user_list/?users=foobar'),
                    )
class UserList(generics.ListAPIView):
    """
    Вывод списка всех пользователей при поиске.
    """
    serializer_class = serializers.UserListSerializer
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        filter_parameter = self.request.query_params.get('users')
        if filter_parameter and len(filter_parameter) > 3:
            queryset = queryset.filter(email__startswith=filter_parameter)
            return queryset
        return None
