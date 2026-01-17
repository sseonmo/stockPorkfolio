from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.stock import StockResponse


class DividendBase(BaseModel):
    stock_id: int
    amount: float = Field(..., description="배당금액 (세전)")
    tax: float = Field(0, description="배당소득세")
    currency: str = Field("KRW", description="통화")
    dividend_date: date = Field(..., description="배당 지급일")
    notes: Optional[str] = None


class DividendCreate(DividendBase):
    pass


class DividendUpdate(BaseModel):
    stock_id: Optional[int] = None
    amount: Optional[float] = None
    tax: Optional[float] = None
    currency: Optional[str] = None
    dividend_date: Optional[date] = None
    notes: Optional[str] = None


class DividendResponse(DividendBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    stock: StockResponse

    model_config = ConfigDict(from_attributes=True)
