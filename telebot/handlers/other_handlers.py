from aiogram import Router, types
from aiogram.methods import SendMessage
from aiogram.types import Message
from telebot.lexicon.lexicon import LEXICON_RU
from aiogram.filters import Command, CommandStart, CommandObject

# Инициализируем роутер уровня модуля
router = Router()


# Этот хэндлер будет срабатывать на любые ваши сообщения,
# кроме команд "/start" и "/help"
@router.message()
async def send_echo(message: Message):
    await message.answer(text=LEXICON_RU['no_answer'])
    await message.delete()


@router.message(Command(prefix='django_', commands='1'))
async def handle_test(request: SendMessage):
    print(f'\n\n{request=}')
