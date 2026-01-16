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
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True)
    quantity: Mapped[float] = mapped_column(Numeric(18, 8), default=0)
    average_cost: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    average_exchange_rate: Mapped[float] = mapped_column(Numeric(10, 4), default=1.0)
    total_invested: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    total_dividends: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    realized_gain: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
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
