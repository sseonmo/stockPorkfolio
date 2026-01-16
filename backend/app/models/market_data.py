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
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True)
    record_date: Mapped[date_type] = mapped_column(Date, index=True)
    
    open_price: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    high_price: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    low_price: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    close_price: Mapped[float] = mapped_column(Numeric(18, 4))
    volume: Mapped[int | None] = mapped_column(nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    stock: Mapped["Stock"] = relationship(back_populates="market_data_history")
