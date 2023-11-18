from rest_framework import generics, viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action

from django.contrib.auth import get_user_model

from taskmanager.email import InviteToWorkspaceEmail
from .models import WorkSpace
from .serializers import WorkSpaceSerializer, CreateWorkSpaceSerializer, WorkSpaceInviteSerializer

User = get_user_model()


class WorkSpaceViewSet(viewsets.ModelViewSet):
    serializer_class = WorkSpaceSerializer
    queryset = WorkSpace.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    ordering_fields = 'created_at'

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateWorkSpaceSerializer
        elif self.action == 'invite_user':
            return WorkSpaceInviteSerializer

        return self.serializer_class

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        queryset = queryset.filter(users=user)
        return queryset

    @action(methods=['patch', 'put'], detail=True)
    def invite_user(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_email = request.POST['email']
        workspace = WorkSpace.objects.get(pk=kwargs['pk'])

        try:
            invite_user = User.objects.get(email=user_email)
            workspace.invited.add(invite_user)
        except User.DoesNotExist:
            user_data = {'email': user_email, 'is_active': False, }
            invite_user = User.objects.create_user(*user_data)
            workspace.invited.add(invite_user)

        context = {'user': invite_user, 'workspace': workspace}
        to = [user_email]
        InviteToWorkspaceEmail(self.request, context).send(to)

        return Response(status=status.HTTP_200_OK)

    # def patch(self, request, *args, **kwargs):
    # 
    #     print(f'{request.data=}\n{kwargs=}')
    #     users = request.data.get('users')
    #     if users:
    #         for n, user in enumerate(users):
    #             if type(user) == str:
    #                 email = users.pop(n)
    #     return super().patch(request, *args, **kwargs)

# class WorkSpaceView(generics.RetrieveUpdateDestroyAPIView):
#     serializer_class = WorkSpaceSerializer
#     queryset = WorkSpace.objects.all()
#     permission_classes = [permissions.IsAuthenticated]
#
#     def patch(self, request, *args, **kwargs):
#
#         print(f'{request.data=}\n{kwargs=}')
#         users = request.data.get('users')
#         if users:
#             for n, user in enumerate(users):
#                 if type(user) == str:
#                     email = users.pop(n)
#         return super().patch(request, *args, **kwargs)
