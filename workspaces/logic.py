from typing import Union, Optional

from workspaces.exeptions import InvalidAction
from django.contrib.auth import get_user_model
from django.db.models import F, Q

from workspaces.models import Column, Task

User = get_user_model()


class WorkSpaceInvite:
    def __init__(self):
        self.workspace = None
        self.user = None
        self.errors = {}

    def invite_user(self, workspace, user_email):
        self.user = self.get_or_create_user(user_email)
        self.workspace = workspace
        self.checking_possibility_invitation()
        self.add_user_in_workspace()
        return self.workspace, self.user

    def add_user_in_workspace(self):
        if self.errors:
            raise InvalidAction(
                detail=self.errors['detail'],
                code=self.errors['code']
            )

        self.workspace.invited.add(self.user)

    def checking_possibility_invitation(self):
        if self.user_is_added_to_workspace():
            self.errors.update({
                'detail': {"email": 'Пользователь уже добавлен в это рабочее пространство'},
                'code': {'already_added'},
            })

        if self.user_is_invited_to_workspace():
            self.errors.update({
                'detail': {"email": 'Пользователь уже приглашен в это рабочее пространство'},
                'code': {'already_invited'},
            })

    def get_or_create_user(self, email: str) -> User:
        """При добавлении пользователя в РП находит указанного пользователя или создает нового"""
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user_data = {'email': email, 'password': None, 'is_active': False, }
            user = User.objects.create_user(**user_data)

        return user

    def user_is_added_to_workspace(self) -> bool:
        if (self.user.id, ) in self.workspace.users.all().values_list('id'):
            return True

        return False

    def user_is_invited_to_workspace(self) -> bool:
        if (self.user.id, ) in self.workspace.invited.all().values_list('id'):
            return True

        return False


class ShiftObjects:
    def __init__(self):
        self.instance = None
        self.objects = None

    def shift(self, objects, instance, new_index, new_col=None):
        self.objects = objects
        self.instance = instance

        if new_col is not None:
            self.delete_shift_index(instance)

        return self._shift_indexes(self.instance, new_index, new_col)

    def _shift_indexes(self,
                       instance: Union[Task, Column],
                       new_index: int,
                       new_col: Optional[Column] = None) -> Union[Task, Column]:
        """Функция пересчитывает порядковые номера обьектов при их перемещении"""
        if new_col is not None and instance.column != new_col:
            self.instance.column = new_col
            instance = self._insert_object(self.instance, new_index)
        elif new_index > self.instance.index:
            instance = self._left_shift(instance, new_index)
        elif new_index < self.instance.index:
            instance = self._right_shift(instance, new_index)

        return instance

    def _insert_object(self, instance: Task, new_index: int) -> Task:
        """Функция перемещения задачи между колонками"""
        # присваиваем индекс None, так как при вставке задачи в новую колонку вставка идет с конца
        instance.index = None
        return self._right_shift(instance, new_index)

    def _left_shift(self, instance: Union[Task, Column], new_index: int) -> Union[Task, Column]:
        """Сдвиг порядковых номеров влево при перемещении обьекта вправо"""
        slice_objects = self.objects[instance.index: new_index + 1]

        for obj in slice_objects:
            if obj == instance:
                obj.index = instance.index = new_index
                continue

            obj.index -= 1
        instance.__class__.objects.bulk_update(slice_objects, ['index'])

        return instance

    def _right_shift(self, instance: Union[Task, Column], new_index: int) -> Union[Task, Column]:
        """Сдвиг порядковых номеров вправо при перемещении обьекта влево"""
        # если индекс None, то пересчет порядковых номеров идет до последнего элемента
        right_border = instance.index + 1 if instance.index is not None else None
        slice_objects = list(self.objects[new_index: right_border])

        for obj in slice_objects:
            if obj == instance:
                obj.index = instance.index = new_index
                continue

            obj.index += 1

        instance.__class__.objects.bulk_update(slice_objects, ['index'])

        return instance

    def delete_shift_index(self, instance: Union[Task, Column]) -> None:
        """Пересчет порядковых номеров при удалении объекта"""
        self.instance = instance
        model_class = self.instance.__class__
        kwargs = self._getkwargs(model_class)

        objs = (model_class.objects
                .filter(index__gte=instance.index + 1)
                .filter(**kwargs)
                )

        objs.update(index=F('index') - 1)

    def _getkwargs(self, model_class):
        if model_class is Column:
            kwargs = {
                'board': self.instance.board
            }
        elif model_class is Task:
            kwargs = {
                'column': self.instance.column
            }
        else:
            assert False, ('Пересчет порядковых номеров осуществляется только'
                           ' для обьектов Task или Column')
        return kwargs
