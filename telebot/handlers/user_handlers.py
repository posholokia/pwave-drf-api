from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from telebot.lexicon.lexicon import LEXICON_RU
from telebot.models import TeleBotID


# Импортируем юзера
User = get_user_model()

# Инициализируем роутер уровня модуля
router = Router()


# Этот хэндлер срабатывает на команду /start
@router.message(CommandStart())
async def process_start_command(message: Message):
    await message.answer(text=f"Отлично, {message.from_user.first_name}!!!\n{LEXICON_RU['/start']}")


# Этот хэндлер срабатывает на команду /mail
@router.message(Command(commands='mail'))
async def process_mail_command(message: Message):
    try:
        if await email_true(message.text.split()[1]):
            await save_telegram_id(message)
            await message.answer(text=LEXICON_RU['mail_changed'])
        else:
            await message.answer(text=LEXICON_RU['mail_not'])
    except IndexError:
        await message.answer(text=LEXICON_RU['mail_empty'])


# Проверка наличия указанной в сообщении почты среди почт наших пользователей.
@sync_to_async
def email_true(email):
    if email in User.objects.all().values_list('email', flat=True):
        return True

# Сохранение
@sync_to_async
def save_telegram_id(message):
    telebotuser=TeleBotID(
        user=User.objects.get(pk=User.objects.get(email=message.text.split()[1]).id),
        telegram_id=message.from_user.id
    )
    telebotuser.save()


# # Этот хэндлер для рассылки всем пользователям бота.
# @router.message(Command(commands='sendall'))
# async def send_all(message: Message):
#     if message.chat.id in #список юзеров с правами админа:
#         await message.answer('Начало рассылки ...')
#         for i in #список пользователей:
#             await bot.send_message(i, message.text[message.text.find(' '):])
#         await message.answer('Рассылка прошла успешно!')
#     else:
#         await message.answer('Скорее всего вы не админ!')