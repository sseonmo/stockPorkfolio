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
    from app.models.dividend import Dividend
    from app.models.stock_daily_performance import StockDailyPerformance


class BaseCurrency(str, enum.Enum):
    KRW = "KRW"
    USD = "USD"


class User(Base):
    __tablename__ = "users"
    __table_args__ = {'comment': '사용자 계정 정보'}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment='사용자 ID (Primary Key)')
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, comment='이메일 (로그인 ID)')
    hashed_password: Mapped[str] = mapped_column(String(255), comment='암호화된 비밀번호')
    name: Mapped[str] = mapped_column(String(100), comment='사용자 이름')
    base_currency: Mapped[BaseCurrency] = mapped_column(
        Enum(BaseCurrency), default=BaseCurrency.KRW, comment='기준 통화 (KRW/USD)'
    )
    is_active: Mapped[bool] = mapped_column(default=True, comment='계정 활성화 여부')
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment='계정 생성일시'
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='마지막 수정일시'
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
    dividends: Mapped[list["Dividend"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    stock_daily_performances: Mapped[list["StockDailyPerformance"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
