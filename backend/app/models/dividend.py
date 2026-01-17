from datetime import date
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.stock import Stock
    from app.models.user import User


class Dividend(Base):
    __tablename__ = "dividends"
    __table_args__ = {'comment': '배당금 수령 내역'}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment='배당 ID (Primary Key)')
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, comment='사용자 ID (FK)')
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True, comment='종목 ID (FK)')
    
    amount: Mapped[float] = mapped_column(Numeric(18, 4), comment='세전 배당금액')
    tax: Mapped[float] = mapped_column(Numeric(18, 4), default=0, comment='배당소득세 (보통 15.4%)')
    currency: Mapped[str] = mapped_column(String(3), default="KRW", comment='통화 단위')
    
    dividend_date: Mapped[date] = mapped_column(Date, index=True, comment='배당 지급일')
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment='메모')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment='등록일시')
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='수정일시')

    # Relationships
    stock: Mapped["Stock"] = relationship(back_populates="dividends")
    user: Mapped["User"] = relationship(back_populates="dividends")
