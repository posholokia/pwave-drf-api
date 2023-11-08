from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from telebot.lexicon.lexicon import LEXICON_RU
#from taskmanager.models import User

# Инициализируем роутер уровня модуля
router = Router()


# Этот хэндлер срабатывает на команду /start
@router.message(CommandStart())
async def process_start_command(message: Message):
    await message.answer(text=f"Отлично, {message.from_user.first_name}!!!\n{LEXICON_RU['/start']}")


# Этот хэндлер срабатывает на команду /mail
@router.message(Command(commands='mail'))
async def process_help_command(message: Message):
#    if message.text.split()[1] ==
    print(message.from_user.id, message.text.split()[1])
    await message.answer(text=LEXICON_RU['mail_changed'])
