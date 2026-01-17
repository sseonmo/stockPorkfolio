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
        {'comment': '일별 포트폴리오 성과 추이'}
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment='성과 ID (Primary Key)')
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, comment='사용자 ID (FK)')
    record_date: Mapped[date_type] = mapped_column(Date, index=True, comment='기준일자')
    
    total_value_krw: Mapped[float] = mapped_column(Numeric(18, 4), comment='총 평가금액 (KRW)')
    total_invested_krw: Mapped[float] = mapped_column(Numeric(18, 4), comment='총 투자원금 (KRW)')
    
    kr_value: Mapped[float] = mapped_column(Numeric(18, 4), default=0, comment='한국 주식 평가금액 (KRW)')
    us_value_usd: Mapped[float] = mapped_column(Numeric(18, 4), default=0, comment='미국 주식 평가금액 (USD)')
    us_value_krw: Mapped[float] = mapped_column(Numeric(18, 4), default=0, comment='미국 주식 평가금액 (KRW)')
    exchange_rate: Mapped[float] = mapped_column(Numeric(10, 4), default=1.0, comment='적용 환율 (USD/KRW)')
    
    daily_pnl: Mapped[float] = mapped_column(Numeric(18, 4), default=0, comment='일일 손익 (전일 대비)')
    daily_pnl_percent: Mapped[float] = mapped_column(Numeric(10, 4), default=0, comment='일일 수익률 (%)')
    cumulative_return: Mapped[float] = mapped_column(Numeric(18, 4), default=0, comment='누적 손익')
    cumulative_return_percent: Mapped[float] = mapped_column(Numeric(10, 4), default=0, comment='누적 수익률 (%)')
    
    total_dividends: Mapped[float] = mapped_column(Numeric(18, 4), default=0, comment='누적 배당금')
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment='기록 생성일시')

    user: Mapped["User"] = relationship(back_populates="daily_performances")
