from datetime import datetime
from datetime import date as date_type
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Date, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class DailyPerformance(Base):
    __tablename__ = "daily_performances"
    __table_args__ = (
        UniqueConstraint("user_id", "record_date", name="uq_user_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    record_date: Mapped[date_type] = mapped_column(Date, index=True)
    
    total_value_krw: Mapped[float] = mapped_column(Numeric(18, 4))
    total_invested_krw: Mapped[float] = mapped_column(Numeric(18, 4))
    
    kr_value: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    us_value_usd: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    us_value_krw: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    exchange_rate: Mapped[float] = mapped_column(Numeric(10, 4), default=1.0)
    
    daily_pnl: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    daily_pnl_percent: Mapped[float] = mapped_column(Numeric(10, 4), default=0)
    cumulative_return: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    cumulative_return_percent: Mapped[float] = mapped_column(Numeric(10, 4), default=0)
    
    total_dividends: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="daily_performances")
