import asyncio
import json
import logging

from redis import asyncio as aioredis

from django.core.management.base import BaseCommand
from django.conf import settings

from aiogram import Bot, Dispatcher

from telebot.config_data.config import Config, load_config
from telebot.handlers import other_handlers, user_handlers
from telebot.handlers.other_handlers import send_notification
from telebot.keyboards.main_menu import set_main_menu

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


# Название класса обязательно - "Command"
class Command(BaseCommand):
    help = 'Just a command for launching a Telegram bot.'

    def handle(self, *args, **kwargs):
        async def main():
            # Загружаем конфиг в переменную config
            config: Config = load_config()

            # Инициализируем бот и диспетчер
            bot = Bot(token=config.tg_bot.token)
            dp = Dispatcher()

            # Регистриуем роутеры в диспетчере
            dp.include_router(user_handlers.router)
            dp.include_router(other_handlers.router)

            # Настраиваем главное меню бота
            await set_main_menu(bot)

            # Пропускаем накопившиеся апдейты и запускаем polling
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info('Запуск телеграм бота')
            await dp.start_polling(bot)

        async def redis_pubsub():
            """Подписка на PubSub Redis для отслеживания уведомлений"""
            logger.info(f'Redis:\n{settings.REDIS_USER=}\n{settings.REDIS_PASS=}\n{settings.REDIS_HOST=}\n{settings.REDIS_PORT=}')
            redis = await aioredis.Redis.from_url(
                (f'redis://{settings.REDIS_USER}:'
                 f'{settings.REDIS_PASS}@'
                 f'{settings.REDIS_HOST}:'
                 f'{settings.REDIS_PORT}/3')
            )
            pub = redis.pubsub()
            await pub.subscribe('notify')
            logger.info('Подписался на PubSub Redis')
            async for msg in pub.listen():
                data = msg.get('data', None)
                if type(data) is bytes:  # при первичном подключении в data будет число
                    data_dict = json.loads(data.decode())
                    message = data_dict.get('message')
                    users = data_dict.get('users')
                    logger.debug(f'Получено уведомление для отправки в '
                                 f'телеграм: {message=} | {users=}')
                    await send_notification(users, message)

        loop = asyncio.get_event_loop()
        # и бот и подписка на pubsub являются блокирующими
        # процессами, поэтому запускаем оба через asyncio.gather
        loop.run_until_complete(asyncio.gather(main(), redis_pubsub()))
        loop.close()
