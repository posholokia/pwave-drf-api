from notification.create_notify.tasks import run_task_notification, run_ws_notification, run_comment_notification, \
    run_del_task_notification
from .utils import get_current_task, get_user_data
from functools import wraps


def send_notify(func):
    """
    декоратор формирует первичные данные и передает их в задачу
    celery, которая запускает формирование уведомлений
    """

    @wraps(func)  # чтобы работало с action декоратором DRF
    def wrapper(*args, **kwargs):
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
    # отправляем в celery создавать уведомления
    # пока нет прокси сервера через celery не будет работать
    if child_obj == 'task' and req['method'] == 'DELETE':
        run_del_task_notification(
            old, user, req
        )
    elif parent_obj == 'task' and child_obj == 'comment':
        run_comment_notification(
            user, req, kwargs.get('task_id')
        )
    elif parent_obj == 'column' and old is not None:  # для задач
        # run_task_notification.apply_async(
        #     (until_change_obj, user, req)
        # )
        run_task_notification(
            old, user, req
        )
    elif parent_obj == 'workspace':  # для РП
        # run_ws_notification.apply_async(
        #     (user, req, kwargs['pk'])
        # )
        run_ws_notification(
            user, req, kwargs['pk']
        )
