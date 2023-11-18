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



@router.message(CommandStart())
async def process_start_command(message: Message):
    """
    Этот хэндлер срабатывает на команду /start.
    """
    await message.answer(text=f"Отлично, {message.from_user.first_name}!!!\n{LEXICON_RU['/start']}")


@router.message(Command(commands='email_add'))
async def process_email_add_command(message: Message):
    """
    Этот хэндлер срабатывает на команду /email_add
    проверяет наличие юзера с такой почтой и при наличии
    добавляет user_id и telegram_id  в табличку TeleBotID.
    """
    try:
        if await _email_true(message.text.split()[1]):
            await _save_telegram_id(message)
            await message.answer(text=LEXICON_RU['mail_changed'])
        else:
            await message.answer(text=LEXICON_RU['mail_not'])
    except IndexError:
        await message.answer(text=LEXICON_RU['mail_empty'])


@router.message(Command(commands='email_delete'))
async def process_email_delete_command(message: Message):
    """
    Этот хэндлер срабатывает на команду /email_delete
    проверяет наличие юзера с такой почтой и при наличии
    удаляет user_id и telegram_id из таблицы TeleBotID.
    """
    try:
        if await _email_true(message.text.split()[1]):
            await _delete_telegram_id(message)
            await message.answer(text=LEXICON_RU['mail_delete'])
        else:
            await message.answer(text=LEXICON_RU['mail_not'])
    except IndexError:
        await message.answer(text=LEXICON_RU['mail_empty'])



@sync_to_async
def _email_true(email):
    """
    Проверка наличия указанной в сообщении почты среди почт наших пользователей.
    """
    if email in User.objects.all().values_list('email', flat=True):
        return True


@sync_to_async
def _save_telegram_id(message):
    """
    Сохраненяет user_id и telegram_id  в табличку TeleBotID.
    """
    telebotuser = TeleBotID(
        user=User.objects.get(pk=User.objects.get(email=message.text.split()[1]).id),
        telegram_id=message.from_user.id
    )
    if not telebotuser.user_id in TeleBotID.objects.all().values_list('user_id', flat=True):
        telebotuser.save()

@sync_to_async
def _delete_telegram_id(message):
    """
    Сохраненяет user_id и telegram_id  в табличку TeleBotID.
    """
    telebotuser = TeleBotID.objects.filter(user=User.objects.get(pk=User.objects.get(email=message.text.split()[1]).id))
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
    await message.answer('Рассылка прошла успешно!')


@sync_to_async
def _give_telebot_id_all():
    """ Возвращает список всех telegram_id из таблицы TeleBotID."""
    return TeleBotID.objects.values('telegram_id')
