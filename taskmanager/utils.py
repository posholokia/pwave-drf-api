from django.core.files.uploadedfile import InMemoryUploadedFile
import tempfile
from PIL import Image
from workspaces.models import WorkSpace, Board


def proportional_reduction(width: int, height: int, max_size: int) -> tuple[int, int]:
    if width <= max_size and height <= max_size:
        return width, height

    larger_side = width if width >= height else height
    proportion = max_size / larger_side
    width = int(round(width * proportion, 0))
    height = int(round(height * proportion, 0))
    return width, height


def get_resized_django_obj(img: Image, width: int, height: int) -> InMemoryUploadedFile:
    """
    Метод преобразует изображение, загруженно пользователем до нужного размера и
    возвращает его в виде объекта Django
    :param img: изображение
    :param width: ширина, рх
    :param height: высота, рх
    :return: InMemoryUploadedFile
    """
    resized_img = img.resize((width, height))  # смена разрешения загруженной картинки
    temp_file = tempfile.NamedTemporaryFile(suffix='.jpg')  # создаем временный файл под аватар
    resized_img.save(temp_file.name)  # сохраняем сокращенное изображение во временный файл
    # преобразование изображения из временного файла в объект модели Джанго
    file = InMemoryUploadedFile(
        file=temp_file,
        field_name=None,
        name=f'NoName',
        content_type='image/jpeg',
        size=temp_file.tell,
        charset=None
    )
    return file


def create_default_ws(user):
    if not user.space_owner.all():
        ws = WorkSpace.objects.create(owner=user, name='Рабочее пространство 1')
        ws.users.add(user)

        board = Board.objects.create(name='Доска 1', work_space=ws)
        board.members.add(user)
