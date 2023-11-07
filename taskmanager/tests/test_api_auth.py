from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from djoser import utils

User = get_user_model()

#
# class UserProfileTestCase(APITestCase):
#     def test_set_password(self):
#         user = User.objects.get(email="testactive@example.com")
#         data = {
#             'new_password': 'Pass!@34',
#             're_new_password': 'Pass!@34',
#             'current_password': 'Pass!234',
#         }
#         response = self.client.post('/auth/users/set_password/', data)
#         self.assertEquals(response.status_code, status.HTTP_200_OK)