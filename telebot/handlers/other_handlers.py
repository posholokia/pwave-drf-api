import os
import re

import aiohttp
from aiogram import Router, Bot
from aiogram.types import Message

from telebot.utils import get_ru_msk_date, formatted_date
from telebot.lexicon.lexicon import LEXICON_RU
from aiogram.utils.markdown import hlink as telegram_link

from telebot.models import TeleBotID

# Инициализируем роутер уровня модуля
router = Router()

bot = Bot(token=os.getenv('BOT_TOKEN'))


# Этот хэндлер будет срабатывать на любые ваши сообщения,
# кроме команд "/start" и "/help"
@router.message()
async def send_echo(message: Message):
    await message.answer(text=LEXICON_RU['no_answer'])
    await message.delete()


async def send_notification(users: list[int], message: str):
    # парсим дату время из сообщения
    message = await formatted_date(message)

    for user in users:
        # отправка сообщений внутри контекстного менеджера,
        # для корректного закрытия соединения после отправки сообщения
        async with aiohttp.ClientSession():
            await bot.send_message(user, message, parse_mode="HTML")

