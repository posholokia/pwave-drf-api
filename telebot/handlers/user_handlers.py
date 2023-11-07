from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from telebot.lexicon.lexicon import LEXICON_RU

# Инициализируем роутер уровня модуля
router = Router()


# Этот хэндлер срабатывает на команду /start
@router.message(CommandStart())
async def process_start_command(message: Message):
    await message.answer(text=f"Отлично, {message.from_user.first_name}!!!\n{LEXICON_RU['/start']}")


# # Этот хэндлер срабатывает на команду /help
# @router.message(Command(commands='help'))
# async def process_help_command(message: Message):
#     await message.answer(text=LEXICON_RU['/help'])
