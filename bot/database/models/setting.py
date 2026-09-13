from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from bot.database.base import Base


class BotSetting(Base):
    __tablename__ = "bot_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")
