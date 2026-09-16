from datetime import datetime
from sqlalchemy import Integer, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from bot.database.base import Base


class UcTariff(Base):
    __tablename__ = "uc_tariffs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uc_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    price_uzs: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
