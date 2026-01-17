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
    from app.models.dividend import Dividend
    from app.models.stock_daily_performance import StockDailyPerformance


class MarketType(str, enum.Enum):
    KR = "KR"
    US = "US"


class Stock(Base):
    __tablename__ = "stocks"
    __table_args__ = {'comment': '주식 종목 마스터 정보'}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment='종목 ID (Primary Key)')
    ticker: Mapped[str] = mapped_column(String(20), unique=True, index=True, comment='종목 코드 (티커)')
    name: Mapped[str] = mapped_column(String(255), comment='종목명')
    market_type: Mapped[MarketType] = mapped_column(Enum(MarketType), index=True, comment='시장 구분 (KR/US)')
    exchange: Mapped[str] = mapped_column(String(50), comment='거래소 (KOSPI/NASDAQ 등)')
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True, comment='업종/섹터')
    current_price: Mapped[float | None] = mapped_column(nullable=True, comment='현재가 (최근 업데이트 가격)')
    currency: Mapped[str] = mapped_column(String(10), default="KRW", comment='통화 단위')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment='등록일시')
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='마지막 수정일시'
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
    dividends: Mapped[list["Dividend"]] = relationship(
        back_populates="stock", cascade="all, delete-orphan"
    )
    stock_daily_performances: Mapped[list["StockDailyPerformance"]] = relationship(
        back_populates="stock", cascade="all, delete-orphan"
    )
