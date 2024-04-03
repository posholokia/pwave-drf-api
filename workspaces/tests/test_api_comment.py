from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken

from workspaces.models import WorkSpace, Board, Column, Task, Sticker, Comment

User = get_user_model()


class TaskTestCase(APITestCase):
    def setUp(self):
        user_data = {
            'email': 'user1@example.com',
            'password': 'Pass!234',
            'is_active': True,
        }
        self.user = User.objects.create_user(**user_data)
        user_token = RefreshToken.for_user(self.user).access_token

        self.ws = WorkSpace.objects.create(owner=self.user, name='WorkSpace1')
        self.ws.users.add(self.user)
        self.board = Board.objects.create(workspace=self.ws, name='Board1')
        self.column1 = Column.objects.create(name='Column1', board=self.board, index=0)
        self.column2 = Column.objects.create(name='Column2', board=self.board, index=1)
        self.task1 = Task.objects.create(name='task1', index=0, column=self.column1)
        self.comment1 = Comment.objects.create(
            task=self.task1,
            author=self.user,
            message='Комментарий 1 для task1 пользователя user')

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'JWT {user_token}')

        user_data2 = {
            'email': 'user2@example.com',
            'password': 'Pass!234',
            'is_active': True,
        }
        self.user2 = User.objects.create_user(**user_data2)
        self.ws2 = WorkSpace.objects.create(owner=self.user, name='WorkSpace2')
        self.ws2.users.add(self.user2)
        self.board2 = Board.objects.create(workspace=self.ws2, name='Board1 WS2')
        self.column3 = Column.objects.create(name='Column1 Board2', board=self.board2, index=0)
        self.task2 = Task.objects.create(name='task2', index=0, column=self.column3)
        self.task3 = Task.objects.create(name='task3', index=1, column=self.column3)

    # тестов не хватает
    def test_comment_create(self):
        data = {
            'task': self.task1.id,  # у тебя таска сама подставляется в комментарий, смысл ее передавать
            'author': self.user.id,  # не нужно его передавать прямо, ведь мы знаем юзера из запроса
            'message': 'Комментарий 2 для task1 пользователя user',
        }
        response = self.client.post(reverse('comment-list', kwargs={'task_id': self.task1.id},), data)
        self.assertEquals(status.HTTP_201_CREATED, response.status_code)
        self.assertEquals(2, len(Comment.objects.filter(task=self.task1.id)))

    def test_fail_comment_create(self):
        pass

    def test_list_comments(self):
        pass

    def test_get_else_comments(self):
        pass

    def test_delete_comment(self):
        pass

    def test_fail_delete_else_comment(self):
        pass



