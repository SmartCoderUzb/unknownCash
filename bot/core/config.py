from pathlib import Path
from typing import List, Any
from zoneinfo import ZoneInfo
from pydantic import Field, AliasChoices, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TASHKENT_TZ = ZoneInfo("Asia/Tashkent")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    # 1. Bot & Admin ma'lumotlari
    BOT_TOKEN: str = Field(default="")
    ADMIN_ID: int = Field(default=0)
    SUPER_ADMINS: Any = Field(
        default_factory=list,
        validation_alias=AliasChoices("SUPER_ADMINS", "ADMINS", "ADMIN_IDS")
    )
    BOT_ID: int = Field(default=1)
    BOT_USERNAME: str = Field(default="")

    # 2. PostgreSQL Database ma'lumotlari
    DB_HOST: str = Field(default="localhost")
    DB_PORT: int = Field(default=5432)
    DB_USER: str = Field(
        default="postgres",
        validation_alias=AliasChoices("DB_USER", "DB_USERNAME", "POSTGRES_USER")
    )
    DB_PASSWORD: str = Field(
        default="",
        validation_alias=AliasChoices("DB_PASSWORD", "DB_PASS", "POSTGRES_PASSWORD")
    )
    DB_NAME: str = Field(
        default="builder_db",
        validation_alias=AliasChoices("DB_NAME", "POSTGRES_DB")
    )
    DATABASE_URL: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DATABASE_URL", "DB_URL", "ASYNC_DATABASE_URL")
    )
    DB_SCHEMA: str | None = Field(default=None)

    # 3. Redis ma'lumotlari
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: str | None = Field(
        default=None,
        validation_alias=AliasChoices("REDIS_PASSWORD", "REDIS_PASS")
    )
    REDIS_URL: str | None = Field(default=None)

    # 4. Dual-Mode Webhook ma'lumotlari
    WEBHOOK_HOST: str | None = Field(default=None)
    WEBHOOK_PATH: str | None = Field(default=None)
    WEBHOOK_URL: str | None = Field(default=None)
    WEBAPP_HOST: str = Field(default="127.0.0.1")
    WEBAPP_PORT: int | None = Field(default=None)

    @field_validator("SUPER_ADMINS", mode="before")
    @classmethod
    def parse_super_admins(cls, v: Any) -> List[int]:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            return [int(x.strip()) for x in v.split(",") if x.strip().isdigit()]
        elif isinstance(v, (list, tuple, set)):
            return [int(x) for x in v if str(x).strip().isdigit()]
        elif isinstance(v, (int, float)):
            return [int(v)]
        return []

    @field_validator("ADMIN_ID", mode="before")
    @classmethod
    def parse_admin_id(cls, v: Any) -> int:
        if isinstance(v, str):
            v = v.strip()
            return int(v) if v.isdigit() else 0
        elif isinstance(v, (int, float)):
            return int(v)
        return 0

    @model_validator(mode="after")
    def compute_defaults(self) -> "Settings":
        # Schema isolation fallback (masalan: uc_bot_1)
        if not self.DB_SCHEMA:
            self.DB_SCHEMA = f"uc_bot_{self.BOT_ID}"

        # Webhook path fallback
        if not self.WEBHOOK_PATH:
            self.WEBHOOK_PATH = f"/webhook/bot/{self.BOT_ID}"

        # Webapp port fallback (10000 + BOT_ID)
        if not self.WEBAPP_PORT:
            self.WEBAPP_PORT = 10000 + int(self.BOT_ID)

        # Webhook URL hisoblash
        if not self.WEBHOOK_URL and self.WEBHOOK_HOST:
            host = self.WEBHOOK_HOST.rstrip("/")
            path = self.WEBHOOK_PATH if self.WEBHOOK_PATH.startswith("/") else f"/{self.WEBHOOK_PATH}"
            self.WEBHOOK_URL = f"{host}{path}"

        # Redis URL hisoblash
        if not self.REDIS_URL:
            if self.REDIS_PASSWORD:
                self.REDIS_URL = f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
            else:
                self.REDIS_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

        return self

    def is_admin(self, user_id: int) -> bool:
        """Foydalanuvchi asosiy admin yoki super adminlar ro'yxatida borligini tekshiradi."""
        if not user_id:
            return False
        if self.ADMIN_ID and user_id == self.ADMIN_ID:
            return True
        if self.SUPER_ADMINS and user_id in self.SUPER_ADMINS:
            return True
        return False

    def get_database_url(self) -> str:
        """Async SQLAlchemy drayveri (asyncpg) uchun to'g'ri ulanish URLini qaytaradi."""
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url

        pwd = f":{self.DB_PASSWORD}" if self.DB_PASSWORD else ""
        return f"postgresql+asyncpg://{self.DB_USER}{pwd}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    def get_redis_url(self) -> str:
        return self.REDIS_URL or f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


settings = Settings()
