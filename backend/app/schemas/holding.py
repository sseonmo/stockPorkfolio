from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.schemas.stock import StockResponse


class HoldingBase(BaseModel):
    stock_id: int
    quantity: float
    average_cost: float
    average_exchange_rate: float = 1.0


class HoldingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    stock_id: int
    quantity: float
    average_cost: float
    average_exchange_rate: float
    total_invested: float
    total_dividends: float
    realized_gain: float
    created_at: datetime
    updated_at: datetime
    stock: StockResponse | None = None


class HoldingWithMetrics(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    stock_id: int
    quantity: float
    average_cost: float
    average_exchange_rate: float
    total_invested: float
    total_dividends: float
    realized_gain: float
    created_at: datetime
    updated_at: datetime
    stock: StockResponse | None = None
    current_value: float
    current_value_krw: float
    unrealized_gain: float
    unrealized_gain_percent: float
    weight_percent: float
