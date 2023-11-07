from aiogram import Router
from aiogram.types import Message
from telebot.lexicon.lexicon import LEXICON_RU

# Инициализируем роутер уровня модуля
router = Router()


# Этот хэндлер будет срабатывать на любые ваши сообщения,
# кроме команд "/start" и "/help"
@router.message()
async def send_echo(message: Message):
    await message.answer(text=LEXICON_RU['no_answer'])
