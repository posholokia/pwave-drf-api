from aiogram import Router
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import Message
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from aiogram.types import CallbackQuery
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

from telebot.keyboards.main_menu import create_menu_keyboard
from telebot.lexicon.lexicon import LEXICON_RU
from telebot.models import TeleBotID
from aiogram.utils.deep_linking import decode_payload

import time

from aiogram import F

# Импортируем юзера
User = get_user_model()

# Инициализируем роутер уровня модуля
router = Router()


@router.message(CommandStart(deep_link=True))
async def process_start_command(message: Message, command: CommandObject):
    """
    Этот хэндлер срабатывает на команду /start в диплинк ссылке
    сохраняет данные юзера либо выводит ошибки.
    """
    try:
        user_id = decode_payload(command.args)
        if await _user_true(user_id):  #Если такого юзера нет совсем в проекте то возвращаем неверная ссылка
            await message.answer(text=LEXICON_RU['token_error'])
            await message.delete()
            return
        if await _telegram_in_table(message) or await _user_in_table(user_id):  #Если у данного юзера или данного телеграмм уже есть запись.
            await message.answer(text=LEXICON_RU['user_in_table'])
        else:
            await _save_telegram_id(message, user_id)  #Сохраняем и отвечаем что уведомления подключены.
            await message.answer(text=LEXICON_RU['mail_changed'])
    except UnicodeDecodeError:  #Ошибка когда несмогли декодировать deeplink
        await message.answer(text=LEXICON_RU['token_error'])
    await message.delete()


@router.message(Command(commands='start'))
async def process_start_command(message: Message):
    """
    Этот хэндлер срабатывает на команду /start.
    """
    await message.answer(text=f"Отлично, {message.from_user.first_name}!!!\n{LEXICON_RU['/start']}")
    await message.delete()


# @router.message(Command(commands='off'))
# async def process_email_delete_command(message: Message):
#     """
#     Этот хэндлер срабатывает на команду /off
#     проверяет наличие юзера с такой почтой и при наличии
#     удаляет user_id и telegram_id из таблицы TeleBotID.
#     """
#     if not await _telegram_in_table(message):
#         await message.answer(text=LEXICON_RU['user_not_in_table'])
#     else:
#         await _delete_telegram_id_off(message)
#         await message.answer(text=LEXICON_RU['mail_delete'])


@router.callback_query(F.data == '/off')
async def process_cancel_press(callback: CallbackQuery):
    """
    Этот хэндлер срабатывает на инлайнкнопку /off
    проверяет наличие юзера с такой почтой и при наличии
    удаляет user_id и telegram_id из таблицы TeleBotID.
    """
    if not await _telegram_in_table(callback):
        await callback.message.edit_text(text=LEXICON_RU['user_not_in_table'])
    else:
        await _delete_telegram_id_off(callback)
        await callback.message.edit_text(text=LEXICON_RU['mail_delete'])
    await callback.answer()


@router.message(Command(commands='menu'))
async def process_email_delete_command(message: Message):
    """
    Этот хэндлер срабатывает на команду /menu
    проверяет наличие юзера с такой почтой и при наличии
    удаляет user_id и telegram_id из таблицы TeleBotID.
    """
    await message.answer(text=LEXICON_RU['menu'], reply_markup=create_menu_keyboard())
    await message.delete()


@sync_to_async
def _user_true(user_id):
    """
    Проверка наличия указанного токена в списке токенов.
    """
    return not User.objects.filter(id=user_id).exists()


@sync_to_async
def _user_in_table(user_id):
    """
    Проверка наличия пользователя в таблице.
    """

    return TeleBotID.objects.filter(user_id=user_id).exists()


@sync_to_async
def _telegram_in_table(message):
    """
    Проверка наличия telegram_id в таблице.
    """
    return TeleBotID.objects.filter(telegram_id=message.from_user.id).exists()


@sync_to_async
def _save_telegram_id(message, user_id):
    """
    Сохраненяет user_id и telegram_id  в табличку TeleBotID.
    """
    telebotuser = TeleBotID(
        user=User.objects.get(id=user_id),
        telegram_id=message.from_user.id,
        name=message.from_user.first_name,
    )
    telebotuser.save()


@sync_to_async
def _delete_telegram_id_off(message):
    """
    Удаляет user_id и telegram_id  в табличку TeleBotID.
    """
    telebotuser = TeleBotID.objects.filter(telegram_id=message.from_user.id)
    telebotuser.delete()


@router.message(Command(commands='sendall'))
async def send_all(message: Message):
    """
    Этот хэндлер срабатывает на команду sendall и рассылает сообщение
    идущее после команды всем пользователям из таблицы TeleBotID.
    """
    await message.answer('Начало рассылки ...')
    async for telegram_id in await _give_telebot_id_all():
        await message.bot.send_message(telegram_id['telegram_id'], message.text[message.text.find(' '):])
        time.sleep(0.1)
    await message.answer('Рассылка прошла успешно!')


@router.message(Command(commands='sendid'))
async def send_id(message: Message):
    """
    Этот хэндлер срабатывает на команду sendid пробел telegram_id и посылает сообщение
    идущее после telegram_id.
    """
    await message.answer(f'Попытка отправки сообщения в чат {message.text.split()[1]}')
    await message.bot.send_message(message.text.split()[1], message.text[message.text.find(message.text.split()[2]):])
    await message.answer('Рассылка прошла успешно!')


@sync_to_async
def _give_telebot_id_all():
    """ Возвращает список всех telegram_id из таблицы TeleBotID."""
    return TeleBotID.objects.values('telegram_id')
