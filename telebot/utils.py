import re

import pytz

from babel.dates import format_datetime

from datetime import datetime


async def formatted_date(message: str) -> str:
    """Проверяем наличие даты в сообщении
    и при наличии форматируем сообщение"""
    data_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}\+\d{4}'
    match = re.search(data_pattern, message)

    if match:  # если спарсили, то меняем часовой пояс на мск
        date_str_utc = match.group(0)
        date_str_msk = await get_ru_msk_date(date_str_utc)
        message = message.replace(date_str_utc, date_str_msk)

    return message


async def get_ru_msk_date(date_str_utc: str) -> str:
    """Преобразование строки c датой из
    UTC в MSK на русском языке"""
    # получение даты из строки
    date = datetime.strptime(
        date_str_utc, '%Y-%m-%dT%H:%M%z'
    )
    # смена часового пояса у даты на мск
    tz = pytz.timezone("Etc/GMT-3")
    date = tz.normalize(date.astimezone(tz))
    # форматирвоание даты в строку на русском
    date_str_msk = format_datetime(
        date, 'd MMMM, H:mm', locale='ru_RU'
    )
    date_str_msk = date_str_msk + ' по МСК'
    return date_str_msk

