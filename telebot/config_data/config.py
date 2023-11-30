import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class TgBot:
    token: str  # Токен для доступа к телеграм-боту


@dataclass
class Config:
    tg_bot: TgBot


def load_config() -> Config:
    return Config(tg_bot=TgBot(token=os.getenv('BOT_TOKEN')))
