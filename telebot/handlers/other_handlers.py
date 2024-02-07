import os
import re

import aiohttp
from aiogram import Router, types, Bot
from aiogram.methods import SendMessage
from aiogram.types import Message
from telebot.lexicon.lexicon import LEXICON_RU
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.utils.markdown import hlink as telegram_link

# Инициализируем роутер уровня модуля
router = Router()

bot = Bot(token=os.getenv('BOT_TOKEN'))


# Этот хэндлер будет срабатывать на любые ваши сообщения,
# кроме команд "/start" и "/help"
@router.message()
async def send_echo(message: Message):
    await message.answer(text=LEXICON_RU['no_answer'])
    await message.delete()


async def send_notification(users: list, message: str):
    ids = [920101866]

    pattern = r'<a\s+href="([^"]+)">([^<]+)</a>'
    match = re.search(pattern, message)

    if match:
        href = match.group(1)
        title = match.group(2)
        link = telegram_link(title, href)
        message = message.replace(match.group(0), link)

    for user_id in ids:
        async with aiohttp.ClientSession():
            await bot.send_message(user_id, message, parse_mode="HTML")

