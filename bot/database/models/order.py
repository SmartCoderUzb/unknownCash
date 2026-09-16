from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Integer, BigInteger, String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bot.database.base import Base

if TYPE_CHECKING:
    from .user import User


class UcOrder(Base):
    __tablename__ = "uc_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    uc_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    price_uzs: Mapped[int] = mapped_column(Integer, nullable=False)
    pubg_id: Mapped[str] = mapped_column(String(64), nullable=False)
    receipt_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending, approved, rejected
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="orders")
