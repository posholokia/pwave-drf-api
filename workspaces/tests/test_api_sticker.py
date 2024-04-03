from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken

from workspaces.models import WorkSpace, Board, Column, Task, Sticker

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
        self.sticker1 = Sticker.objects.create(name='sticker1', color='#FA1', task=self.task1)

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

    def test_sticker_create(self):
        data = {
            'name': 'new sticker',
            'color': '#AD45E4',
            'task': self.task1.id,
        }
        response = self.client.post(reverse('sticker-list', kwargs={'task_id': self.task1.id}), data)
        self.assertEquals(status.HTTP_201_CREATED, response.status_code)
        self.assertEquals(2, len(Sticker.objects.filter(task=self.task1.id)))

    def test_sticker_else_create(self):
        data = {
            'name': 'new sticker',
            'color': '#AD45E4',
            'task': self.task3.id,
        }
        response = self.client.post(reverse('sticker-list', kwargs={'task_id': self.task3.id}), data)
        self.assertEquals(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEquals(0, len(Sticker.objects.filter(task=self.task3.id)))

    def test_get_sticker_list(self):
        Sticker.objects.create(name='sticker2', color='#FA1', task=self.task1)

        response = self.client.get(reverse('sticker-list', kwargs={'task_id': self.task1.id}))
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertEquals(2, len(response.data))

    def test_get_sticker(self):
        response = self.client.get(
            reverse('sticker-detail', kwargs={'task_id': self.task1.id, 'pk': self.sticker1.id})
        )
        self.assertEquals(status.HTTP_200_OK, response.status_code)

    def test_patch_sticker(self):
        data = {
            'color': '#AD45E4',
        }
        response = self.client.patch(
            reverse('sticker-detail', kwargs={'task_id': self.task1.id, 'pk': self.sticker1.id}),
            data
        )
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.sticker1.refresh_from_db()
        self.assertEquals('#AD45E4', self.sticker1.color)

    def test_put_sticker(self):
        data = {
            'name': 'new',
            'color': '#AD45E4',
        }
        response = self.client.put(
            reverse('sticker-detail', kwargs={'task_id': self.task1.id, 'pk': self.sticker1.id}),
            data
        )
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.sticker1.refresh_from_db()
        self.assertEquals('#AD45E4', self.sticker1.color)
        self.assertEquals('new', self.sticker1.name)

    def test_delete_sticker(self):
        response = self.client.delete(
            reverse('sticker-detail', kwargs={'task_id': self.task1.id, 'pk': self.sticker1.id}),
        )
        self.assertEquals(status.HTTP_204_NO_CONTENT, response.status_code)

    def test_bad_color(self):
        data = {
            'color': '#RED',
        }
        response = self.client.patch(
            reverse('sticker-detail', kwargs={'task_id': self.task1.id, 'pk': self.sticker1.id}),
            data
        )
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.sticker1.refresh_from_db()
        self.assertEquals('#FA1', self.sticker1.color)