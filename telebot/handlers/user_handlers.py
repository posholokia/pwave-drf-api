from concurrent.futures import thread

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from taskmanager.models import User

from telebot.lexicon.lexicon import LEXICON_RU


# Инициализируем роутер уровня модуля
router = Router()
#User = get_user_model()

# Этот хэндлер срабатывает на команду /start
@router.message(CommandStart())
async def process_start_command(message: Message):
    await message.answer(text=f"Отлично, {message.from_user.first_name}!!!\n{LEXICON_RU['/start']}")


# Этот хэндлер срабатывает на команду /mail
@router.message(Command(commands='mail'))
async def process_mail_command(message: Message):
    try:
        if await email_true(message.text.split()[1]):
            print(message.text.split()[1])
            await message.answer(text=LEXICON_RU['mail_changed'])
        else:
            await message.answer(text=LEXICON_RU['mail_not'])
    except IndexError:
        await message.answer(text=LEXICON_RU['mail_empty'])


@sync_to_async
def email_true(email):
    if email in User.objects.all().values_list('email', flat=True):
        return True
