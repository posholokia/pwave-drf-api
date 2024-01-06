from typing import Union, Optional

from django.contrib.auth import get_user_model
from django.db.models import F
from django.db.models.query import QuerySet

from workspaces.models import Column, Task

User = get_user_model()


class ShiftObjects:
    def __init__(self):
        self.instance = None
        self.objects = None

    def shift(self,
              objects: QuerySet,
              instance: Union[Task, Column],
              new_index: int,
              new_col=None) -> Union[Task, Column]:
        self.objects = objects
        self.instance = instance

        if self.is_new_column(new_col):
            self.delete_shift_index(instance)

        return self._shift_indexes(self.instance, new_index, new_col)

    def _shift_indexes(self,
                       instance: Union[Task, Column],
                       new_index: int,
                       new_col: Optional[Column] = None) -> Union[Task, Column]:
        """Функция пересчитывает порядковые номера обьектов при их перемещении"""
        if self.is_new_column(new_col):
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

    def _getkwargs(self, model_class: Union[Task, Column]) -> dict:
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

    def is_new_column(self, new_col: Column) -> bool:
        if new_col is not None and self.instance.column != new_col:
            return True
        else:
            return False


index_recalculation = ShiftObjects()
