from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken

from workspaces.models import WorkSpace, Board

User = get_user_model()


class BoardTestCase(APITestCase):
    def setUp(self):
        user_data = {
            'email': 'user1@example.com',
            'password': 'Pass!234',
            'is_active': True,
        }
        self.user = User.objects.create_user(**user_data)
        self.user.save()
        user_token = RefreshToken.for_user(self.user).access_token

        self.ws = WorkSpace.objects.create(owner=self.user, name='WorkSpace1')
        self.ws.users.add(self.user)
        self.board = Board.objects.create(work_space=self.ws, name='Board1')
        self.board.save()

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'JWT {user_token}')

    def test_board_create(self):
        data = {
            'work_space': self.ws.id,
            'name': 'My Board'
        }
        response = self.client.post(reverse('boards-list'), data)
        self.assertEquals(status.HTTP_201_CREATED, response.status_code)
        self.assertEquals(2, len(Board.objects.all()))

    def test_board_create_fail_name(self):
        data = {
            'name': 'My Board name is very, very long, longer than necessary'
        }

        response = self.client.post(reverse('boards-list'), data)
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)
        error_code = response.data['name'][0].code
        self.assertEquals('max_length', error_code)

    def test_board_get_list(self):
        response = self.client.get(reverse('boards-list'))
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertEquals(1, len(response.data))

    def test_get_board(self):
        response = self.client.get(reverse('boards-detail', kwargs={'pk': self.board.id}))
        self.assertEquals(status.HTTP_200_OK, response.status_code)

    def test_patch_board(self):
        data = {
            'name': 'Changed name',
        }
        response = self.client.patch(reverse('boards-detail', kwargs={'pk': self.board.id}),
                                     data=data)
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.board.refresh_from_db()
        self.assertEquals('Changed name', self.board.name)

    def test_put_board(self):
        data = {
            'name': 'Changed name',
        }
        response = self.client.put(reverse('boards-detail', kwargs={'pk': self.board.id}),
                                   data=data)
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.board.refresh_from_db()
        self.assertEquals('Changed name', self.board.name)

    def test_delete_board(self):
        response = self.client.delete(reverse('boards-detail', kwargs={'pk': self.board.id}))
        self.assertEquals(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertEquals(0, len(self.user.joined_workspaces.get(pk=self.ws.id).board.all()))

