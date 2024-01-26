import datetime

from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from django.urls import reverse
from freezegun import freeze_time

from notification.models import Notification
from workspaces.models import WorkSpace, Board, Column, Task

User = get_user_model()


class NotificationTestCase(APITestCase):
    def setUp(self):
        user_data = {
            'email': 'user1@example.com',
            'password': 'Pass!234',
            'is_active': True,
        }
        self.user1 = User.objects.create_user(**user_data)
        self.user2 = User.objects.create_user(email='user2@example.com')
        self.user3 = User.objects.create_user(email='user3@example.com')
        self.user4 = User.objects.create_user(email='user4@example.com')
        self.user5 = User.objects.create_user(email='user5@example.com')

        self.ws1 = WorkSpace.objects.create(owner=self.user1, name='WorkSpace1')
        self.ws1.users.set([self.user1, self.user2, self.user3])
        self.board1 = Board.objects.create(work_space=self.ws1, name='Board1')
        self.board2 = Board.objects.create(work_space=self.ws1, name='Board2')
        self.column1board1 = Column.objects.get(board=self.board1, name='Готово')
        self.column1board2 = Column.objects.get(board=self.board2, name='Готово')
        self.column2board1 = Column.objects.get(board=self.board1, name='В работе')

        self.task1 = Task.objects.create(name='Task1', column=self.column1board1, index=0)
        self.task2 = Task.objects.create(name='Task2', column=self.column1board1, index=1)
        self.task3 = Task.objects.create(name='Task3', column=self.column1board2, index=0)
        self.task4 = Task.objects.create(name='Task4', column=self.column1board2, index=1)
        self.task1.responsible.add(self.user1)
        self.task2.responsible.add(self.user1)
        self.task3.responsible.add(self.user1)
        self.task4.responsible.add(self.user1)

        # self.ws2 = WorkSpace.objects.create(owner=self.user4, name='WorkSpace2')
        # self.ws2.users.set([self.user1, self.user4, self.user5])
        # self.board3 = Board.objects.create(work_space=self.ws2, name='Board3')
        # self.column1board3 = Column.objects.get(board=self.board3, name='Готово')
        # self.task11 = Task.objects.create(name='Task1', column=self.column1board3, index=0)
        # self.task12 = Task.objects.create(name='Task2', column=self.column1board3, index=1)
        # self.task11.responsible.add(self.user1)
        # self.task12.responsible.add(self.user1)

        self.client = APIClient()
        self.client.force_authenticate(self.user1)

    def test_added_in_ws(self):
        data = {'email': 'user5@example.com'}
        self.client.post(reverse('workspace-invite_user', kwargs={'pk': self.ws1.id}), data)
        self.assertEquals(True, Notification.objects.filter(workspace=self.ws1).exists())
        n = Notification.objects.get(workspace=self.ws1)
        users = list(n.recipients.all())
        self.assertEquals(self.user5, *users)

    def test_del_from_ws(self):
        data = {'user_id': self.user3.id}
        self.client.post(reverse('workspace-kick_user', kwargs={'pk': self.ws1.id}), data)
        self.assertEquals(True, Notification.objects.filter(workspace=self.ws1).exists())
        n = Notification.objects.get(workspace=self.ws1)
        users = list(n.recipients.all())
        self.assertEquals(self.user3, *users)

    def test_added_in_task(self):
        u = list(self.task1.responsible.values_list('id', flat=True))
        u.append(self.user2.id)
        u.append(self.user3.id)
        data = {'responsible': u}
        self.client.patch(
            reverse('task-detail',
                    kwargs={'pk': self.task1.id, 'column_id': self.column1board1.id}),
            data
        )
        self.assertEquals(True, Notification.objects.filter(workspace=self.ws1).exists())
        n = Notification.objects.get(workspace=self.ws1)
        users = list(n.recipients.values_list('id', flat=True))
        self.assertEquals([self.user2.id, self.user3.id], users)

    def test_delete_from_task(self):
        u = [self.user1.id, self.user2.id]
        self.task1.responsible.set(u)
        data = {'responsible': [self.user1.id]}
        self.client.patch(
            reverse('task-detail',
                    kwargs={'pk': self.task1.id, 'column_id': self.column1board1.id}),
            data
        )
        self.assertEquals(True, Notification.objects.filter(workspace=self.ws1).exists())
        n = Notification.objects.get(workspace=self.ws1)
        users = list(n.recipients.values_list('id', flat=True))
        self.assertEquals([self.user2.id], users)

    def test_deadline_task(self):
        self.task1.responsible.add(self.user3)
        data = {'deadline': "2024-01-26T16:27Z"}
        self.client.patch(
            reverse('task-detail',
                    kwargs={'pk': self.task1.id, 'column_id': self.column1board1.id}),
            data
        )
        self.assertEquals(True, Notification.objects.filter(workspace=self.ws1).exists())
        n = Notification.objects.get(workspace=self.ws1)
        users = list(n.recipients.values_list('id', flat=True))
        self.assertEquals([self.user3.id], users)

    def test_change_deadline(self):
        self.task1.responsible.add(self.user2)
        self.task1.deadline = datetime.datetime.now()
        data = {'deadline': "2024-01-26T16:27Z"}
        self.client.patch(
            reverse('task-detail',
                    kwargs={'pk': self.task1.id, 'column_id': self.column1board1.id}),
            data
        )
        self.assertEquals(True, Notification.objects.filter(workspace=self.ws1).exists())
        n = Notification.objects.get(workspace=self.ws1)
        users = list(n.recipients.values_list('id', flat=True))
        self.assertEquals([self.user2.id], users)

    def test_move_task(self):
        self.task1.responsible.add(self.user3)
        data = {'index': 0, 'column': self.column2board1.id}
        self.client.patch(
            reverse('task-detail',
                    kwargs={'pk': self.task1.id, 'column_id': self.column1board1.id}),
            data
        )
        self.assertEquals(True, Notification.objects.filter(workspace=self.ws1).exists())
        n = Notification.objects.get(workspace=self.ws1)
        users = list(n.recipients.values_list('id', flat=True))
        self.assertEquals([self.user3.id], users)

    def test_delete_task(self):
        self.task1.responsible.add(self.user2)
        self.client.delete(
            reverse(
                'task-detail',
                kwargs={'pk': self.task1.id, 'column_id': self.column1board1.id}
            ),
        )
        self.assertEquals(True, Notification.objects.filter(workspace=self.ws1).exists())
        n = Notification.objects.get(workspace=self.ws1)
        users = list(n.recipients.values_list('id', flat=True))
        self.assertEquals([self.user2.id], users)

    def test_change_name(self):
        self.task1.responsible.add(self.user2)
        data = {'name': 'Super Task!'}
        self.client.patch(
            reverse(
                'task-detail',
                kwargs={'pk': self.task1.id, 'column_id': self.column1board1.id}
            ),
            data,
        )
        self.assertEquals(True, Notification.objects.filter(workspace=self.ws1).exists())
        n = Notification.objects.get(workspace=self.ws1)
        users = list(n.recipients.values_list('id', flat=True))
        self.assertEquals([self.user2.id], users)

    def test_change_priority(self):
        self.task1.responsible.add(self.user3)
        data = {'priority': 3}
        self.client.patch(
            reverse(
                'task-detail',
                kwargs={'pk': self.task1.id, 'column_id': self.column1board1.id}
            ),
            data,
        )
        self.assertEquals(True, Notification.objects.filter(workspace=self.ws1).exists())
        n = Notification.objects.get(workspace=self.ws1)
        users = list(n.recipients.values_list('id', flat=True))
        self.assertEquals([self.user3.id], users)

    def test_end_deadline(self):
        pass
