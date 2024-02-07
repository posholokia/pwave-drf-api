from notification.create_notify.tasks import run_task_notification, run_ws_notification
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
        path_obj = request.path.split('/')[2]
        user = get_user_data(request.user)

        if path_obj == 'column':  # сохраняем текущее состояние таски
            until_change_obj = get_current_task(kwargs.get('pk'))

        res = func(*args, **kwargs)

        status = res.status_code
        allow_status = [200, 201, 204, ]

        # если метод выполнен успешно
        if status in allow_status:
            req = {
                'data': request.data,
                'method': request.method,
            }
            # отправляем в celery создавать уведомления
            # пока нет прокси сервера через celery не будет работать
            if path_obj == 'column' and until_change_obj is not None:  # для задач
                # run_task_notification.apply_async(
                #     (until_change_obj, user, req)
                # )
                run_task_notification(
                    until_change_obj, user, req
                )
            elif path_obj == 'workspace':  # для РП
                # run_ws_notification.apply_async(
                #     (user, req, kwargs['pk'])
                # )
                run_ws_notification(
                    user, req, kwargs['pk']
                )
        return res

    return wrapper