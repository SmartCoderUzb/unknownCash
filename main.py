import asyncio
import logging
import signal
import sys
from aiohttp import web
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from bot.core.config import settings
from bot.core.loader import bot, dp, storage
from bot.database.session import init_db, async_session, engine
from bot.database import crud
from bot.middlewares import DbSessionMiddleware, UserTrackerMiddleware
from bot.handlers import common_router, admin_router, user_router

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Main")


async def setup_commands():
    """Telegram bot buyruqlar menyusini sozlaydi."""
    commands = [
        BotCommand(command="start", description="Botni ishga tushirish / Bosh menyu"),
        BotCommand(command="panel", description="Admin paneli"),
    ]
    try:
        await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    except Exception as e:
        logger.warning(f"Buyruqlarni o'rnatishda ogohlantirish: {e}")


async def main():
    # 1. BOT_TOKEN tekshiruvi
    if not settings.BOT_TOKEN or ":" not in settings.BOT_TOKEN:
        logger.error("BOT_TOKEN ko'rsatilmagan yoki noto'g'ri! Iltimos, .env faylida bot tokeningizni kiriting.")
        return

    logger.info(f"Bot ishga tushirilmoqda... [BOT_ID={settings.BOT_ID}, SCHEMA={settings.DB_SCHEMA}]")

    # 2. PostgreSQL Schema Isolation va jadvallarni initsializatsiya qilish
    await init_db()
    async with async_session() as session:
        await crud.init_default_settings(session)
        # Asosiy adminni bazada admin sifatida belgilash
        owner_id = settings.ADMIN_ID or (settings.SUPER_ADMINS[0] if settings.SUPER_ADMINS else 0)
        if owner_id:
            user, _ = await crud.get_or_create_user(
                session=session,
                user_id=owner_id,
                username=None,
                first_name="Bot Egasi"
            )
            user.is_admin = True
            await session.commit()

    # 3. Middlewares ro'yxatdan o'tkazish
    dp.update.middleware(DbSessionMiddleware(session_pool=async_session))
    dp.update.middleware(UserTrackerMiddleware())

    # 4. Routers ro'yxatdan o'tkazish
    dp.include_router(common_router)
    dp.include_router(admin_router)
    dp.include_router(user_router)

    # 5. Buyruqlarni o'rnatish
    await setup_commands()

    # 6. Bot ma'lumotlarini olish va Readiness Probe
    me = await bot.get_me()
    # Shartnoma bo'yicha platforma aynan shu satr orqali bot 100% faollashganini aniqlaydi:
    print(f"Bot muvaffaqiyatli ishga tushdi: @{me.username}", flush=True)

    # 7. Dual-Mode: Webhook yoki Polling
    if settings.WEBHOOK_URL:
        logger.info(
            f"Webhook rejimida ishga tushmoqda: {settings.WEBHOOK_URL} "
            f"({settings.WEBAPP_HOST}:{settings.WEBAPP_PORT})"
        )
        app = web.Application()
        SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=settings.WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host=settings.WEBAPP_HOST, port=settings.WEBAPP_PORT)
        await site.start()

        await bot.set_webhook(
            url=settings.WEBHOOK_URL,
            drop_pending_updates=True,
            allowed_updates=dp.resolve_used_update_types()
        )

        stop_event = asyncio.Event()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_event.set)

        await stop_event.wait()

        logger.info("Bot to'xtatilmoqda...")
        await bot.delete_webhook()
        await runner.cleanup()
    else:
        logger.info("Polling rejimida ishga tushmoqda...")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(
            bot,
            drop_pending_updates=True,
            allowed_updates=dp.resolve_used_update_types()
        )

    # Graceful shutdown
    if storage:
        await storage.close()
    await bot.session.close()
    await engine.dispose()
    logger.info("Bot muvaffaqiyatli to'xtatildi.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
