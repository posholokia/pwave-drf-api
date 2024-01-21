from notification.create_notify.tasks import create_notification
from .utils import get_task_data, get_ws_data
from functools import wraps


def task_change_notify(func):
    """
    декоратор методов viewset Task для
    создания уведомлений
    """
    def wrapper(*args, **kwargs):
        # получаем данные для создания уведомления
        data = get_task_data(*args, **kwargs)
        res = func(*args, **kwargs)
        status = res.status_code
        allow_status = [200, 201, 204, ]

        # если метод выполнен успешно
        if status in allow_status:
            # отправляем в celery создавать уведомления
            create_notification.apply_async((data, ))
        return res

    return wrapper


def ws_users_notify(func):
    """
    декоратор методов viewset WorkSpace для
    создания уведомлений
    """
    @wraps(func)  # чтобы работало с action декоратором DRF
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)

        # если метод выполнен успешно
        if res.status_code == 200:
            # получаем данные для создания уведомления
            data = get_ws_data(*args, **kwargs)
            # отправляем в celery создавать уведомления
            create_notification.apply_async((data, ))
        return res

    return wrapper

