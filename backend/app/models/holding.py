from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.stock import Stock


class Holding(Base):
    __tablename__ = "holdings"
    __table_args__ = (
        UniqueConstraint("user_id", "stock_id", name="uq_user_stock"),
        {'comment': '사용자별 보유 종목 현황 (포지션)'}
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment='보유 종목 ID (Primary Key)')
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, comment='사용자 ID (FK)')
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True, comment='종목 ID (FK)')
    quantity: Mapped[float] = mapped_column(Numeric(18, 8), default=0, comment='보유 수량')
    average_cost: Mapped[float] = mapped_column(Numeric(18, 4), default=0, comment='평균 매수 단가')
    average_exchange_rate: Mapped[float] = mapped_column(Numeric(10, 4), default=1.0, comment='평균 매수 환율')
    total_invested: Mapped[float] = mapped_column(Numeric(18, 4), default=0, comment='총 투자금액 (KRW)')
    total_dividends: Mapped[float] = mapped_column(Numeric(18, 4), default=0, comment='누적 배당금 (KRW)')
    realized_gain: Mapped[float] = mapped_column(Numeric(18, 4), default=0, comment='실현 손익 (매도 확정 금액)')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment='최초 매수일시')
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='마지막 거래 반영일시'
    )

    user: Mapped["User"] = relationship(back_populates="holdings")
    stock: Mapped["Stock"] = relationship(back_populates="holdings")

    @property
    def current_value(self) -> float:
        if self.stock and self.stock.current_price:
            return float(self.quantity) * self.stock.current_price
        return 0.0

    @property
    def unrealized_gain(self) -> float:
        return self.current_value - float(self.total_invested)

    @property
    def unrealized_gain_percent(self) -> float:
        if float(self.total_invested) > 0:
            return (self.unrealized_gain / float(self.total_invested)) * 100
        return 0.0
