from django.core.files.uploadedfile import InMemoryUploadedFile
import tempfile
from PIL import Image
from rest_framework import exceptions


class AvatarUpload:
    """
    Аватар пользователя пропорционально уменьшается до self.max_size
    для хранения его в хранилище
    """
    def __init__(self):
        self.avatar = None
        self.name = None
        self.width = None
        self.height = None
        self.max_size = 200

    def get_resized_img(self, avatar):
        self.name = avatar.name
        with Image.open(avatar.file) as img:
            self.avatar = img
            self._avatar_handler()
            return self.avatar

    def _avatar_handler(self):
        if self.avatar:
            self._proportional_reduction()
            self._check_size()
            self._get_resized_django_obj()

    def _proportional_reduction(self) -> None:
        """
        Пропорционально сужает значения ширины и высоты изображения,
        чтобы стороны не превышали максимальный размер
        """
        width, height = self.avatar.size
        if width <= self.max_size and height <= self.max_size:
            self.width = width
            self.height = height
        else:
            larger_side = width if width >= height else height
            proportion = self.max_size / larger_side
            self.width = int(round(width * proportion, 0))
            self.height = int(round(height * proportion, 0))

    def _check_size(self):
        if self.width < 55 or self.height < 55:
            raise exceptions.ValidationError(
                {'avatar': 'Слишком низкое качество изображения . '
                           'Допустимое разрешение не меньше 55х55', }
            )

    def _get_resized_django_obj(self):
        """
        Метод преобразует изображение, загруженно пользователем до нужного размера и
        возвращает его в виде объекта Django
        """
        resized_img = self.avatar.resize((self.width, self.height))  # смена разрешения загруженной картинки
        temp_file = tempfile.NamedTemporaryFile(suffix='.png')  # создаем временный файл под аватар
        resized_img.save(temp_file.name)  # сохраняем сокращенное изображение во временный файл
        # преобразование изображения из временного файла в объект модели Джанго
        file = InMemoryUploadedFile(
            file=temp_file,
            field_name=None,
            name=f'{self.name}',
            content_type='image/png',
            size=temp_file.tell,
            charset=None
        )
        self.avatar = file
