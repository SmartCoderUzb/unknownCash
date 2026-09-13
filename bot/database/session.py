import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)
from bot.core.config import settings, BASE_DIR
from bot.database.base import Base

logger = logging.getLogger("DatabaseSession")

is_pg = "postgresql" in settings.get_database_url()
schema = settings.DB_SCHEMA

connect_args = {
    "server_settings": {
        "search_path": f'"{schema}", public'
    }
} if (is_pg and schema) else {}

engine = create_async_engine(
    settings.get_database_url(),
    echo=False,
    pool_pre_ping=True,
    connect_args=connect_args
)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    """
    Bot ishga tushganda CREATE SCHEMA IF NOT EXISTS \"{DB_SCHEMA}\" buyrug'ini bajaradi
    va barcha jadvallarni faqat shu schema ichida yaratadi (SET search_path TO \"{DB_SCHEMA}\").
    """
    global engine
    import bot.database.models  # Modellarni ro'yxatdan o'tkazish

    try:
        async with engine.begin() as conn:
            if "postgresql" in engine.url.drivername and schema:
                await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
                await conn.execute(text(f'SET search_path TO "{schema}"'))
            await conn.run_sync(Base.metadata.create_all)
        logger.info(f"Ma'lumotlar bazasi muvaffaqiyatli initsializatsiya qilindi (schema: {schema}).")
    except Exception as e:
        logger.warning(f"PostgreSQL ulanishida ogohlantirish ({e}).")
        if "postgresql" in engine.url.drivername:
            # Fallback to local SQLite if postgres server is offline
            (BASE_DIR / "data").mkdir(exist_ok=True)
            sqlite_file = f"bot_{settings.BOT_ID}.db"
            sqlite_url = f"sqlite+aiosqlite:///{BASE_DIR}/data/{sqlite_file}"
            logger.info(f"SQLite fallback rejimiga o'tilmoqda: data/{sqlite_file}")
            engine = create_async_engine(sqlite_url, echo=False)
            async_session.configure(bind=engine)
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("SQLite bazasi muvaffaqiyatli initsializatsiya qilindi.")
        else:
            raise e
