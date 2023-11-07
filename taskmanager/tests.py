from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from djoser import utils

User = get_user_model()


class RegistrationTestCase(APITestCase):
    def setUp(self):
        data = {
            'email': 'testuser1@example.com',
            'password': r'Pass!234',
            'is_active': False,
        }
        User.objects.create(**data)

        data = {
            'email': 'testactive@example.com',
            'password': r'Pass!234',
            'is_active': True,
        }
        User.objects.create(**data)

    def test_success_registration(self):
        data = {
            'email': 'ilya.posholokk@gmail.com',
            'password': r'Pass12346579!@#$%^&*-_+=[](){}|;:\,.<>?',
            're_password': r'Pass12346579!@#$%^&*-_+=[](){}|;:\,.<>?',
            'subscriber': True,
        }
        response = self.client.post('/auth/users/', data)
        self.assertEquals(status.HTTP_201_CREATED, response.status_code)

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

    def test_resend_activation(self):
        data = {"email": "testuser1@example.com"}
        response = self.client.post('/auth/users/resend_activation/', data)
        self.assertEquals(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_activation_confirm(self):
        user = User.objects.get(email="testuser1@example.com")
        token = default_token_generator.make_token(user)
        uid = utils.encode_uid(user.pk)
        data = {
            'uid': uid,
            'token': token,
        }
        response = self.client.post('/auth/users/activation/', data)
        self.assertEquals(response.status_code, status.HTTP_200_OK)


class UserProfileTestCase(APITestCase):
    def test_set_password(self):
        user = User.objects.get(email="testactive@example.com")
        data = {
            'new_password': 'Pass!@34',
            're_new_password': 'Pass!@34',
            'current_password': 'Pass!234',
        }
        response = self.client.post('/auth/users/set_password/', data)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
