import json

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from djoser import utils
from djoser.serializers import UserCreatePasswordRetypeSerializer
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from taskmanager.serializers import CurrentUserSerializer


User = get_user_model()


class RegistrationTestCase(APITestCase):
    def setUp(self):
        inactive_user = {
            'email': 'test-inctive-user@example.com',
            'password': 'Pass!234',
            'is_active': False,
        }
        self.user_not_active = User.objects.create_user(**inactive_user)
        self.token_na = default_token_generator.make_token(self.user_not_active)
        self.uid_na = utils.encode_uid(self.user_not_active.pk)

        active_user = {
            'email': 'test-active-user@example.com',
            'password': 'Pass!234',
            'is_active': True,
        }
        self.user_active = User.objects.create_user(**active_user)
        self.token_a = default_token_generator.make_token(self.user_active)
        self.uid_a = utils.encode_uid(self.user_active.pk)

    def test_success_registration(self):
        data = {
            'email': 'ilya.posholokk@gmail.com',
            'password': r'Pass12346579!@#$%^&*-_+=[](){}|;:\,.<>?',
            're_password': r'Pass12346579!@#$%^&*-_+=[](){}|;:\,.<>?',
            'subscriber': True,
        }
        response = self.client.post('/auth/users/', data)
        self.assertEquals(status.HTTP_201_CREATED, response.status_code)
        self.assertEquals(3, len(User.objects.all()))

    def test_pass_validator(self):
        data = {'email': 'ilya.posholokk@gmail.com',}
        data['password'] = data['re_password'] = 'Iв1*R;$'
        response = self.client.post('/auth/users/', data)
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)  # пароль короткий
        data['password'] = data['re_password'] = 'Ig!@kERV$'
        response = self.client.post('/auth/users/', data)
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)  # пароль без цифр
        data['password'] = data['re_password'] = 'ig!@kerv321$'
        response = self.client.post('/auth/users/', data)
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)  # пароль без заглавных символов
        data['password'] = data['re_password'] = 'IG!@KERV$13'
        response = self.client.post('/auth/users/', data)
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)  # пароль без строчных букв
        data['password'] = data['re_password'] = 'IGraKERVr13'
        response = self.client.post('/auth/users/', data)
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)  # пароль без спец. символов
        data['password'] = data['re_password'] = ''
        response = self.client.post('/auth/users/', data)
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)  # пустые пароли
        data['password'], data['re_password'] = ('IG#$KERVr13', 'IG#$KERVr1')
        response = self.client.post('/auth/users/', data)
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)  # разные пароли
        data.pop('re_password')
        response = self.client.post('/auth/users/', data)
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)  # регистрация без повтора пароля

    def test_resend_activation(self):
        data = {'email': 'test-inctive-user@example.com'}
        response = self.client.post('/auth/users/resend_activation/', data)
        self.assertEquals(status.HTTP_204_NO_CONTENT, response.status_code)  # юзер не активен

        data = {'email': 'test-active-user@example.com'}
        response = self.client.post('/auth/users/resend_activation/', data)
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)  # юзер активен

        data = {'email': 'user-does-not-exists@example.com'}
        response = self.client.post('/auth/users/resend_activation/', data)
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)  # юзер не существует

    def test_activation_confirm(self):
        data = {
            'uid':  self.uid_na,
            'token': self.token_na,
        }

        response = self.client.post('/auth/users/activation/', data)
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.user_not_active.refresh_from_db()
        self.assertEquals(True, self.user_not_active.is_active)
        self.assertEquals(['refresh', 'access'], list(response.data.keys()))  # выданы токены

    def test_reset_password(self):
        data = {'email': 'test-inctive-user@example.com'}
        response = self.client.post('/auth/users/reset_password/', data)
        self.assertEquals(status.HTTP_204_NO_CONTENT, response.status_code)  # юзер не активен

        data = {'email': 'test-active-user@example.com'}
        response = self.client.post('/auth/users/reset_password/', data)
        self.assertEquals(status.HTTP_204_NO_CONTENT, response.status_code)  # юзер активен

    def test_reset_pass_confirm(self):
        data = {
            'uid':  self.uid_na,
            'token': self.token_na,
            'new_password': 'Qaщй12*-',
            're_new_password': 'Qaщй12*-'
        }
        response = self.client.post('/auth/users/reset_password_confirm/', data)
        self.user_not_active.refresh_from_db()
        self.assertEquals(status.HTTP_204_NO_CONTENT, response.status_code)  # юзер не активен
        self.assertEquals(True, self.user_not_active.is_active)  # после смены пароля активировался

        data = {
            'uid': self.uid_a,
            'token': self.token_a,
            'new_password': 'Qaщй12*-',
            're_new_password': 'Qaщй12*-'
        }
        response = self.client.post('/auth/users/reset_password_confirm/', data)
        self.assertEquals(status.HTTP_204_NO_CONTENT, response.status_code)  # юзер активен

    def test_jwt_create(self):
        data = {
            'email': 'test-active-user@example.com',
            'password': r'Pass!234',
        }
        response = self.client.post(reverse('jwt-create'), data)
        self.assertEquals(status.HTTP_200_OK, response.status_code)  # юзер активен
        self.assertEquals(['refresh', 'access'], list(response.data.keys()))  # выданы токены

        data = {
            'email': 'test-inctive-user@example.com',
            'password': r'Pass!234',
        }
        self.user_not_active.refresh_from_db()
        response = self.client.post(reverse('jwt-create'), data)
        self.assertEquals(status.HTTP_401_UNAUTHORIZED, response.status_code)  # юзер не активен

    def test_jwt_refresh(self):
        refresh = RefreshToken.for_user(self.user_active)
        data = {'refresh': str(refresh)}
        response = self.client.post(reverse('jwt-refresh'), data)
        self.assertEquals(status.HTTP_200_OK, response.status_code)

    def test_jwt_verify(self):
        refresh = RefreshToken.for_user(self.user_active)
        access = refresh.access_token
        data = {'token': str(refresh)}
        response = self.client.post(reverse('jwt-verify'), data)
        self.assertEquals(status.HTTP_200_OK, response.status_code)

        data = {'token': str(access)}
        response = self.client.post(reverse('jwt-verify'), data)
        self.assertEquals(status.HTTP_200_OK, response.status_code)

    def test_jwt_blacklist(self):
        refresh = RefreshToken.for_user(self.user_active)
        data = {'refresh': str(refresh)}
        response = self.client.post(reverse('token_blacklist'), data)
        self.assertEquals(status.HTTP_200_OK, response.status_code)

        refresh = OutstandingToken.objects.get(token=str(refresh))
        blocked_tokens = BlacklistedToken.objects.values_list('token_id', )
        self.assertIn((refresh.id, ), blocked_tokens)

    def test_check_link(self):
        data = {
            'uid': self.uid_na,
            'token': self.token_na,
        }
        response = self.client.post('/auth/users/check_link/', data)
        self.assertEquals(status.HTTP_204_NO_CONTENT, response.status_code)  # позитивный тест

        data = {
            'uid': self.uid_a,
            'token': self.token_na,
        }
        response = self.client.post('/auth/users/check_link/', data)
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)  # негативный тест
