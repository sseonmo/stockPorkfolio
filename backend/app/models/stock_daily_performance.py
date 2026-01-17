from datetime import datetime
from datetime import date as date_type
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Date, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.stock import Stock


class StockDailyPerformance(Base):
    __tablename__ = "stock_daily_performances"
    __table_args__ = (
        UniqueConstraint("user_id", "stock_id", "record_date", name="uq_user_stock_date"),
        {'comment': '종목별 일일 성과 (일별 손익)'}
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment='성과 ID (Primary Key)')
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, comment='사용자 ID (FK)')
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True, comment='종목 ID (FK)')
    record_date: Mapped[date_type] = mapped_column(Date, index=True, comment='기준일자')
    
    quantity: Mapped[float] = mapped_column(Numeric(18, 8), comment='당일 보유수량')
    close_price: Mapped[float] = mapped_column(Numeric(18, 4), comment='당일 종가')
    prev_close_price: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True, comment='전일 종가')
    
    daily_pnl: Mapped[float] = mapped_column(Numeric(18, 4), default=0, comment='일일 손익 (전일 대비)')
    daily_pnl_percent: Mapped[float] = mapped_column(Numeric(10, 4), default=0, comment='일일 수익률 (%)')
    
    position_value: Mapped[float] = mapped_column(Numeric(18, 4), default=0, comment='보유금액 (종가 기준)')
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment='기록 생성일시')

    user: Mapped["User"] = relationship(back_populates="stock_daily_performances")
    stock: Mapped["Stock"] = relationship(back_populates="stock_daily_performances")
