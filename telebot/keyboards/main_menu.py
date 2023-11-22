from aiogram import Bot
from aiogram.types import BotCommand
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from telebot.lexicon.lexicon import LEXICON_COMMANDS


# Функция для настройки кнопки Menu бота
async def set_main_menu(bot: Bot):
    main_menu_commands = [BotCommand(
        command=command,
        description=description
    ) for command,
        description in LEXICON_COMMANDS.items()]
    await bot.set_my_commands(main_menu_commands)


# Функция создания инлайн кнопок главного меню
def create_menu_keyboard() -> InlineKeyboardMarkup:
    # Создаем объект клавиатуры
    kb_builder = InlineKeyboardBuilder()
    # Наполняем клавиатуру кнопками-закладками в порядке возрастания
    kb_builder.row(
        InlineKeyboardButton(text=LEXICON_COMMANDS['delete'], callback_data='/off'),
    )
    return kb_builder.as_markup()