from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from workspaces.models import WorkSpace

User = get_user_model()


class BoardTestCase(APITestCase):
    def setUp(self):
        user_data = {
            'email': 'user1@example.com',
            'password': 'Pass!234',
            'is_active': True,
        }
        self.user = User.objects.create_user(**user_data)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_ws_create(self):
        data = {
            'name': 'My WorkSpace'
        }
        response = self.client.post(reverse('workspace-list'), data)
        self.assertEquals(status.HTTP_201_CREATED, response.status_code)
        self.assertEquals(1, len(WorkSpace.objects.all()))

    def test_ws_get_list(self):
        pass

    def test_get_ws(self):
        pass

    def test_patch_ws(self):
        pass

    def test_put_ws(self):
        pass

    def test_delete_ws(self):
        pass

    def test_invite_user(self):
        pass

    def test_kick_user(self):
        pass

    def test_resend_invite(self):
        pass

    def test_confirm_invite(self):
        pass
