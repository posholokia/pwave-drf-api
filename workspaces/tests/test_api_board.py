from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


class WorkSpaceTestCase(APITestCase):
    def setUp(self):
        pass

    def test_board_create(self):
        pass

    def test_board_get_list(self):
        pass

    def test_get_board(self):
        pass

    def test_patch_board(self):
        pass

    def test_put_board(self):
        pass

    def test_delete_board(self):
        pass
