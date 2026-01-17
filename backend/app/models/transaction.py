from datetime import datetime
from datetime import date as date_type
from typing import TYPE_CHECKING
import enum

from sqlalchemy import String, DateTime, Date, ForeignKey, Enum, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.stock import Stock


class TransactionType(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = {'comment': '매매 거래 내역 (매수/매도)'}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment='거래 ID (Primary Key)')
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, comment='사용자 ID (FK)')
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True, comment='종목 ID (FK)')
    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), comment='거래 유형 (BUY/SELL/DIVIDEND)')
    quantity: Mapped[float] = mapped_column(Numeric(18, 8), comment='거래 수량')
    price: Mapped[float] = mapped_column(Numeric(18, 4), comment='거래 단가')
    exchange_rate: Mapped[float] = mapped_column(Numeric(10, 4), default=1.0, comment='환율 (USD->KRW)')
    fees: Mapped[float] = mapped_column(Numeric(18, 4), default=0.0, comment='수수료')
    transaction_date: Mapped[date_type] = mapped_column(Date, index=True, comment='거래 일자')
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True, comment='메모')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment='등록일시')

    user: Mapped["User"] = relationship(back_populates="transactions")
    stock: Mapped["Stock"] = relationship(back_populates="transactions")

    @property
    def total_amount(self) -> float:
        return float(self.quantity) * float(self.price)

    @property
    def total_amount_krw(self) -> float:
        return self.total_amount * float(self.exchange_rate)
