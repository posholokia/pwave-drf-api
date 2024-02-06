from django_eventstream import send_event

from sse.senders import sse_send_board, sse_send_task
from sse.utils import get_board_id, get_task_id


def sse_create(event_type=None):
    """
    Декортатор для create, update и destroy методов view для отправки SSE.
    Работает для всего содержимого доски и через SSE отправляет обновленную доску.
    """
    assert type(event_type) is list, 'event_type должно быть списком строк'
    assert {*event_type} <= {'workspace', 'board', 'task'}, \
        ('Неверно указан тип события для отправки события'
         'Допустимые события: workspace, board, task')

    def decorator(func):
        def wrapper(*args, **kwargs):
            path = args[1].path

            # вызов метода и в переменную res записываем Response метода
            res = func(*args, **kwargs)

            # достаем статус ответа и данные из Response
            status = res.status_code
            allow_status = [200, 201, 204]

            # если апи вернул ошибку, событие не отправляем
            if status not in allow_status:
                return res

            if 'board' in event_type:
                board_id = get_board_id(path)

                if board_id is not None:
                    sse_send_board(board_id, *args)

            if 'task' in event_type:
                task_id = get_task_id(path)

                if task_id is not None:
                    sse_send_task(task_id, *args)

            return res
        return wrapper
    return decorator
