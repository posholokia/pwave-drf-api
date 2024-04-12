import logging

from django.contrib.auth import get_user_model

from notification.create_notify.tasks import run_task_notification, run_ws_notification, run_comment_notification, \
    run_del_task_notification
from .utils import get_user_data, get_pre_inintial_data
from functools import wraps

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

User = get_user_model()


def task_notification(func):
    """
    Запуск celery таски для создания уведомления об изменении/удалении задачи
    """
    @wraps(func)  # чтобы работало с action декоратором DCRF
    def wrapper(*args, **kwargs):
        logger.info(f'Вызван декоратор уведомления об изменении/удалении задачи')
        user_obj = args[0].scope["user"]
        user, old_task = get_pre_inintial_data(user_obj, kwargs.get('pk'))
        res = func(*args, **kwargs)

        if kwargs.get('action') == 'patch':
            run_task_notification.apply_async(
                (old_task, user, kwargs.get('data'))
            )
            logger.info(f'Отправлена задача в celery. patch task {old_task=}, {user=}')
        elif kwargs.get('action') == 'delete':
            run_del_task_notification.apply_async(
                (old_task, user)
            )
            logger.info(f'Отправлена задача в celery. delete task {old_task=}, {user=}')

        return res
    return wrapper


def comment_notification(func):
    """
    Запуск celery таски для создания уведомления о добавлении комментария
    """
    @wraps(func)  # чтобы работало с action декоратором DCRF
    def wrapper(*args, **kwargs):
        request = args[1]
        user_obj = request.user
        data = request.data
        user = get_user_data(user_obj)

        res = func(*args, **kwargs)

        run_comment_notification.apply_async(
            (user, data, kwargs.get('task_id'))
        )

        return res
    return wrapper


def workspace_notification(func):
    """
    Запуск celery таски для создания уведомления о приглашении/удалении из РП
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        request = args[1]
        user_obj = request.user
        data = request.data
        user = get_user_data(user_obj)

        res = func(*args, **kwargs)

        run_ws_notification.apply_async(
            (user, data, kwargs['pk'])
        )
        return res
    return wrapper
