from datetime import datetime
from datetime import date as date_type
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Date, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.stock import Stock


class MarketDataHistory(Base):
    __tablename__ = "market_data_history"
    __table_args__ = (
        UniqueConstraint("stock_id", "record_date", name="uq_stock_date"),
        {'comment': '종목별 일별 시세 이력 (OHLCV)'}
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment='시세 ID (Primary Key)')
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True, comment='종목 ID (FK)')
    record_date: Mapped[date_type] = mapped_column(Date, index=True, comment='기준일자')
    
    open_price: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True, comment='시가')
    high_price: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True, comment='고가')
    low_price: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True, comment='저가')
    close_price: Mapped[float] = mapped_column(Numeric(18, 4), comment='종가')
    volume: Mapped[int | None] = mapped_column(nullable=True, comment='거래량')
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment='데이터 수집일시')

    stock: Mapped["Stock"] = relationship(back_populates="market_data_history")
