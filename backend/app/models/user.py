from datetime import datetime
from typing import TYPE_CHECKING
import enum

from sqlalchemy import String, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.transaction import Transaction
    from app.models.holding import Holding
    from app.models.daily_performance import DailyPerformance


class BaseCurrency(str, enum.Enum):
    KRW = "KRW"
    USD = "USD"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(100))
    base_currency: Mapped[BaseCurrency] = mapped_column(
        Enum(BaseCurrency), default=BaseCurrency.KRW
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    holdings: Mapped[list["Holding"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    daily_performances: Mapped[list["DailyPerformance"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
