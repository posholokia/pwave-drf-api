from notification.create_notify.tasks import create_notification
from .utils import get_task_data, get_ws_data
from functools import wraps


def task_change_notify(func):
    def wrapper(*args, **kwargs):
        data = get_task_data(*args, **kwargs)
        res = func(*args, **kwargs)
        status = res.status_code
        allow_status = [200, 201, 204, ]

        if status in allow_status:
            create_notification.apply_async((data, ))
        return res

    return wrapper


def ws_users_notify(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)

        if res.status_code == 200:
            data = get_ws_data(*args, **kwargs)
            create_notification.apply_async((data, ))
        return res

    return wrapper

