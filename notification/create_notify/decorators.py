import logging

from django.contrib.auth import get_user_model

from notification.create_notify.tasks import run_task_notification, run_ws_notification, run_comment_notification, \
    run_del_task_notification
from .utils import get_current_task, get_user_data, get_pre_inintial_data
from functools import wraps

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

User = get_user_model()


def send_notify(func):
    """
    декоратор формирует первичные данные и передает их в задачу
    celery, которая запускает формирование уведомлений
    """

    @wraps(func)  # чтобы работало с action декоратором DRF
    def wrapper(*args, **kwargs):
        logger.info(f'Вызов декоратора для создания уведомлений')
        # получаем данные для создания уведомления
        request = args[1]
        parent_obj = request.path.split('/')[2]
        child_obj = request.path.split('/')[4]
        user = get_user_data(request.user)

        internal_kwargs = kwargs.copy()

        # сохраняем текущее состояние таски до того
        # как изменится после выполнения request
        if parent_obj == 'column':
            old_obj = get_current_task(kwargs.get('pk'))
            internal_kwargs.update({'old': old_obj})

        res = func(*args, **kwargs)

        status = res.status_code
        allow_status = [200, 201, 204, ]
        # если метод выполнен успешно
        if status in allow_status:
            req = {
                'data': request.data,
                'method': request.method,
            }

            notification_distributor(parent_obj,
                                     child_obj,
                                     req,
                                     user,
                                     **internal_kwargs)

        return res

    return wrapper


def notification_distributor(parent_obj,
                             child_obj,
                             req,
                             user,
                             **kwargs):
    """Распределение уведомлений по хэндлерам"""
    old = kwargs.get('old', None)
    logger.info(f'Распределяем данные для создания уведомлений по хэндлерам')
    # отправляем в celery создавать уведомления
    # пока нет прокси сервера через celery не будет работать
    if child_obj == 'task' and req['method'] == 'DELETE':
        logger.info(f'Отправка в хэндлер удаления задачи')
        run_del_task_notification.apply_async(
            (old, user)
        )

    elif parent_obj == 'task' and child_obj == 'comment':
        logger.info(f'Отправка в хэндлер уведолмение о комментарии')
        run_comment_notification.apply_async(
            (user, req, kwargs.get('task_id'))
        )

    elif parent_obj == 'column' and old is not None:  # для задач
        logger.info(f'Отправка в хэндлер изменения задачи')
        run_task_notification.apply_async(
            (old, user, req)
        )

    elif parent_obj == 'workspace':  # для РП
        logger.info(f'Отправка в хэндлер рабочего пространства')
        run_ws_notification.apply_async(
            (user, req, kwargs['pk'])
        )


def task_notification(func):
    @wraps(func)  # чтобы работало с action декоратором DCRF
    def wrapper(*args, **kwargs):
        user_obj = args[0].scope["user"]
        user, old_task = get_pre_inintial_data(user_obj, kwargs.get('pk'))
        res = func(*args, **kwargs)

        if kwargs.get('action') == 'patch':
            run_task_notification.apply_async(
                (old_task, user, kwargs.get('data'))
            )
        elif kwargs.get('action') == 'delete':
            run_del_task_notification.apply_async(
                (old_task, user)
            )

        return res
    return wrapper
