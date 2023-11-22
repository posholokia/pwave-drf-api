from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from aiogram.types import CallbackQuery
from telebot.keyboards.main_menu import create_menu_keyboard
from telebot.lexicon.lexicon import LEXICON_RU
from telebot.models import TeleBotID
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
import time

from aiogram import F

# Импортируем юзера
User = get_user_model()

# Инициализируем роутер уровня модуля
router = Router()


@router.message(CommandStart(deep_link=True))
async def process_start_command(message: Message):
    """
    Этот хэндлер срабатывает на команду /start в диплинк ссылке и если префикс
    on - включает уведомления
    off - выключает уведомления.
    """
    if await _token_true(message):
        if message.text.split('_')[0] == '/start on':
            if await _telegram_in_table(message):
                await message.answer(text=LEXICON_RU['user_in_table'])
            else:
                if await _user_in_table(message):
                    await message.answer(text=LEXICON_RU['user_in_table'])
                else:
                    await _save_telegram_id(message)
                    await message.answer(text=LEXICON_RU['mail_changed'])

        # if message.text.split('_')[0] == '/start off':
        #     if not await _telegram_in_table(message):
        #         await message.answer(text=LEXICON_RU['user_not_in_table'])
        #     else:
        #         await _delete_telegram_id(message)
        #         await message.answer(text=LEXICON_RU['mail_delete'])
    else:
        await message.answer(text=LEXICON_RU['token_error'])


@router.message(Command(commands='start'))
async def process_start_command(message: Message):
    """
    Этот хэндлер срабатывает на команду /start.
    """
    await message.answer(text=f"Отлично, {message.from_user.first_name}!!!\n{LEXICON_RU['/start']}")


# @router.message(Command(commands='on')) # не работает нужно переделать
# async def process_email_add_command(message: Message):
#     """
#     Этот хэндлер срабатывает на команду /on
#     проверяет наличие юзера с такой почтой и при наличии
#     добавляет user_id и telegram_id  в табличку TeleBotID.
#     """
#     try:
#         if await _email_true(message.text.split()[1]):
#             if not await _user_in_table(message):
#                 print('Почта ок')
#                 if not await _telegram_in_table(message):
#                     print('токена нет')
#                     await message.answer(text=LEXICON_RU['mail_changed'])
#                     await _save_telegram_id(message)
#                     print('Сохранение прошло')
#                     await message.answer(text=LEXICON_RU['mail_changed'])
#                 else:
#                     await message.answer(text=LEXICON_RU['user_in_table'])
#             else:
#                 await message.answer(text=LEXICON_RU['user_in_table'])
#         else:
#             await message.answer(text=LEXICON_RU['mail_not'])
#     except IndexError:
#         await message.answer(text=LEXICON_RU['mail_empty'])


@router.message(Command(commands='off'))
async def process_email_delete_command(message: Message):
    """
    Этот хэндлер срабатывает на команду /off
    проверяет наличие юзера с такой почтой и при наличии
    удаляет user_id и telegram_id из таблицы TeleBotID.
    """
    if not await _telegram_in_table(message):
        await message.answer(text=LEXICON_RU['user_not_in_table'])
    else:
        await _delete_telegram_id_off(message)
        await message.answer(text=LEXICON_RU['mail_delete'])


@router.callback_query(F.data == '/off')
async def process_cancel_press(callback: CallbackQuery):
    """
    Этот хэндлер срабатывает на инлайнкнопку /off
    проверяет наличие юзера с такой почтой и при наличии
    удаляет user_id и telegram_id из таблицы TeleBotID.
    """
    if not await _telegram_in_table(callback):
        await callback.edit_text(text=LEXICON_RU['user_not_in_table'])
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


# @sync_to_async
# def _email_true(email):
#     """
#     Проверка наличия указанной в сообщении почты среди почт наших пользователей.
#     """
#     if email in User.objects.all().values_list('email', flat=True):
#         return True

@sync_to_async
def _token_true(message):
    """
    Проверка наличия указанного токена в списке токенов.
    """
    if message.text.split('_')[1] in OutstandingToken.objects.all().values_list('token', flat=True):
        return True


@sync_to_async
def _user_in_table(message):
    """
    Проверка наличия пользователя в таблице.
    """
    if User.objects.get(pk=OutstandingToken.objects.get(token=message.text.split('_')[1]).user_id) \
            in TeleBotID.objects.all().values_list('user_id', flat=True):
        return True


@sync_to_async
def _telegram_in_table(message):
    """
    Проверка наличия telegram_id в таблице.
    """
    if message.from_user.id in TeleBotID.objects.all().values_list('telegram_id', flat=True):
        return True


@sync_to_async
def _save_telegram_id(message):
    """
    Сохраненяет user_id и telegram_id  в табличку TeleBotID.
    """
    telebotuser = TeleBotID(
        user=User.objects.get(pk=OutstandingToken.objects.get(token=message.text.split('_')[1]).user_id),
        telegram_id=message.from_user.id,
        telegram_name=message.from_user.username
    )
    telebotuser.save()


# @sync_to_async
# def _delete_telegram_id(message):
#     """
#     Сохраненяет user_id и telegram_id в табличку TeleBotID для диплинк ссылки.
#     """
#     telebotuser = TeleBotID.objects.filter(
#         user=User.objects.get(
#             pk=OutstandingToken.objects.get(
#                 token=message.text.split('_')[1]).user_id
#         )
#     )
#     telebotuser.delete()


@sync_to_async
def _delete_telegram_id_off(message):
    """
    Сохраненяет user_id и telegram_id  в табличку TeleBotID.
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
