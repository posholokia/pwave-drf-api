from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from taskmanager.token import token_generator
from taskmanager.serializers import CurrentUserSerializer
User = get_user_model()


class UserProfileTestCase(APITestCase):
    def setUp(self):
        user_data = {
            'email': 'test-user@example.com',
            'password': 'Pass!234',
            'is_active': True,
        }
        self.user = User.objects.create_user(**user_data)
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.user_id = self.user.id

    def test_users_id_get(self):
        response = self.client.get(f'/auth/users/{self.user_id}/')
        self.assertEquals(status.HTTP_200_OK, response.status_code)

        expected_data = {
            'id': self.user_id,
            'email': 'test-user@example.com',
            'name': '',
            'represent_name': 'test-user',
            'avatar': None,
        }

        serializer_data = CurrentUserSerializer(self.user).data
        self.assertEquals(expected_data, serializer_data)

    def test_users_id_put(self):
        data = {
            'id': 1234,
            'name': 'Илья',
            'email': 'new-email@example.com',
        }
        response = self.client.put(f'/auth/users/{self.user_id}/', data)
        self.user.refresh_from_db()
        self.assertEquals('Илья', self.user.name)  # имя изменилось
        self.assertNotEquals(1234, self.user.id)  # id не изменился
        self.assertEquals('test-user@example.com', self.user.email)  # почта не изменилась
        self.assertEquals(status.HTTP_200_OK, response.status_code)

    def test_users_id_patch(self):
        data = {
            'name': 'Илья',
        }
        response = self.client.patch(f'/auth/users/{self.user_id}/', data)
        self.user.refresh_from_db()
        self.assertEquals('Илья', self.user.name)
        self.assertEquals(status.HTTP_200_OK, response.status_code)

    def test_users_id_delete(self):
        data = {
            'current_password': 'Pass!2345',
        }
        response = self.client.delete(f'/auth/users/{self.user_id}/', data)
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)  # фейл тест должен быть до успешного

        data['current_password'] = 'Pass!234'
        response = self.client.delete(f'/auth/users/{self.user_id}/', data)
        self.assertEquals(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertEquals(0, len(User.objects.all()))

    def test_change_email(self):
        user_data = {
            'password': 'Pass!234',
            'email': 'mymail@example.com',
        }
        User.objects.create_user(**user_data)

        data = {
            'password': 'Pass!234',
            'new_email': 'new-email@example.com',
        }
        response = self.client.post(reverse('change_email'), data)
        self.user.refresh_from_db()
        self.assertEquals('test-user@example.com', self.user.email)  # почта не изменилась
        self.assertEquals(status.HTTP_204_NO_CONTENT, response.status_code)

        data = {
            'password': 'Pass!234',
            'new_email': 'test-user@example.com',
        }
        response = self.client.post(reverse('change_email'), data)
        self.user.refresh_from_db()
        self.assertEquals('test-user@example.com', self.user.email)  # почта не изменилась
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)  # нельзя сменить почту на такую же

        data = {
            'password': 'Pass!234',
            'new_email': 'mymail@example.com',
        }
        response = self.client.post(reverse('change_email'), data)
        self.user.refresh_from_db()
        self.assertEquals('test-user@example.com', self.user.email)  # почта не изменилась
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)  # почта уникальна

    def test_change_email_confirm(self):
        payload = {
            'user_id': self.user_id,
            'current_email': self.user.email,
            'new_email': 'new-email@example.com',
        }
        token = token_generator.token_encode(payload)
        response = self.client.post(reverse('change_email_confirm'), {'token': token})
        self.user.refresh_from_db()
        self.assertEquals('new-email@example.com', self.user.email)  # почта изменилась
        self.assertEquals(status.HTTP_204_NO_CONTENT, response.status_code)

    def test_users_get(self):
        user_data = {
            'email': 'test2-user@example.com',
            'password': 'Pass!234',
            'is_active': True,
        }
        User.objects.create_user(**user_data)
        response = self.client.get('/auth/users/')
        self.assertEquals(1, len(response.data))  # возвращает только текущего юзера, а не всех
        self.assertEquals(status.HTTP_200_OK, response.status_code)

    def test_set_password(self):
        data = {
            'new_password': 'Pass!234',
            're_new_password': 'Pass!234',
            'current_password': 'Pass!234',
        }
        response = self.client.post('/auth/users/set_password/', data)
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)

        data = {
            'new_password': 'Pass!234*',
            're_new_password': 'Pass!234*',
            'current_password': 'Pass!234',
        }
        response = self.client.post('/auth/users/set_password/', data)
        self.assertEquals(status.HTTP_204_NO_CONTENT, response.status_code)
        self.user.refresh_from_db()
        password_changed = self.user.check_password('Pass!234*')
        self.assertEquals(True, password_changed)
