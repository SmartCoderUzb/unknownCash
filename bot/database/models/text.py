from sqlalchemy import String, Text, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column
from bot.database.base import Base


class BotText(Base):
    __tablename__ = "bot_texts"
    __table_args__ = (PrimaryKeyConstraint("key", "type"),)

    key: Mapped[str] = mapped_column(String(64))
    type: Mapped[str] = mapped_column(String(16), default="text")  # "text" yoki "button"
    value: Mapped[str] = mapped_column(Text, default="")
