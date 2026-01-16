from datetime import datetime
from typing import TYPE_CHECKING
import enum

from sqlalchemy import String, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.transaction import Transaction
    from app.models.holding import Holding
    from app.models.market_data import MarketDataHistory


class MarketType(str, enum.Enum):
    KR = "KR"
    US = "US"


class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    market_type: Mapped[MarketType] = mapped_column(Enum(MarketType), index=True)
    exchange: Mapped[str] = mapped_column(String(50))
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    current_price: Mapped[float | None] = mapped_column(nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="KRW")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="stock", cascade="all, delete-orphan"
    )
    holdings: Mapped[list["Holding"]] = relationship(
        back_populates="stock", cascade="all, delete-orphan"
    )
    market_data_history: Mapped[list["MarketDataHistory"]] = relationship(
        back_populates="stock", cascade="all, delete-orphan"
    )
