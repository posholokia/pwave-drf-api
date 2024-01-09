from django_eventstream import send_event


def sse_send(func):
    """
    Декортатор create, update и destroy методов view, создает SSE.
    При вызове декорируемых методов создает событие с данными,
    которые возвращает сам метод.
    Канал отправки и тип события базируется на url из request.
    Так как url построены по принципу parent/id/child/id,
    при изменении child во view в качестве ответа возвращается весь массив child обьектов.
    """
    def wrapper(*args, **kwargs):
        path = args[1].path.split('/')  # получает url в котором был изменен обьект
        obj = path[2]  # это родительский обьект (связан с измененным через FK),
        obj_id = path[3]
        changed_obj = path[-3]

        prefix = ''
        if changed_obj == obj:
            prefix = 'update_'

        # вызов метода и в переменную res записываем Response метода
        res = func(*args, **kwargs)

        # достаем статус ответа и данные из Response
        status = res.status_code
        data = res.data

        # если метод выполнен успешно, отправляем событие всем слушателям
        if status == 201 or status == 200:
            send_event(f'{prefix}{obj}', f'{obj}-{obj_id}', data)

        return res
    return wrapper
