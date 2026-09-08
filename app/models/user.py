# app/models/user.py
import enum
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserRole(str, enum.Enum):
    OWNER = "OWNER"
    MANAGER = "MANAGER"
    FINANCIER = "FINANCIER"
    STOCKMAN = "STOCKMAN"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.STOCKMAN, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} role={self.role} tg={self.telegram_id}>"
