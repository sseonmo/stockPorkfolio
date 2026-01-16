from datetime import datetime
from pydantic import BaseModel

from app.models.stock import MarketType


class StockBase(BaseModel):
    ticker: str
    name: str
    market_type: MarketType
    exchange: str
    sector: str | None = None


class StockCreate(StockBase):
    pass


class StockUpdate(BaseModel):
    name: str | None = None
    sector: str | None = None
    current_price: float | None = None


class StockResponse(StockBase):
    id: int
    current_price: float | None
    currency: str
    created_at: datetime

    class Config:
        from_attributes = True


class StockSearchResult(BaseModel):
    ticker: str
    name: str
    market_type: MarketType
    exchange: str
    current_price: float | None = None
