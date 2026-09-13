import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from bot.core.config import settings

logger = logging.getLogger("BotLoader")

bot_token = settings.BOT_TOKEN
if not bot_token or ":" not in bot_token:
    bot_token = "1234567890:AAFakeTokenForModuleImportPurposes12345"

# 1. Bot initsializatsiyasi
bot = Bot(
    token=bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# 2. Redis FSM Storage: DefaultKeyBuilder(with_bot_id=True, prefix=settings.DB_SCHEMA)
def get_storage():
    try:
        key_builder = DefaultKeyBuilder(
            with_bot_id=True,
            prefix=settings.DB_SCHEMA
        )
        storage = RedisStorage.from_url(
            url=settings.get_redis_url(),
            key_builder=key_builder
        )
        return storage
    except Exception as e:
        logger.warning(f"Redis initsializatsiyasida ogohlantirish ({e}). MemoryStorage ga o'tilmoqda.")
        return MemoryStorage()

storage = get_storage()

# 3. Dispatcher initsializatsiyasi
dp = Dispatcher(storage=storage)

__all__ = ["bot", "dp", "storage", "settings", "get_storage"]
