from sqlalchemy import BigInteger, Column, DateTime, String, func
from bot.database.base import Base


class Admin(Base):
    __tablename__ = "admins"

    user_id = Column(BigInteger, primary_key=True)
    role = Column(String(32), default="admin", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
