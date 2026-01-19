from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict

from app.models.transaction import TransactionType
from app.schemas.stock import StockResponse


class TransactionBase(BaseModel):
    stock_id: int
    transaction_type: TransactionType
    quantity: float = Field(gt=0)
    price: float = Field(gt=0)
    exchange_rate: float = Field(default=1.0, gt=0)
    fees: float = Field(default=0.0, ge=0)
    transaction_date: date
    notes: str | None = None


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    quantity: float | None = Field(default=None, gt=0)
    price: float | None = Field(default=None, gt=0)
    exchange_rate: float | None = Field(default=None, gt=0)
    fees: float | None = Field(default=None, ge=0)
    transaction_date: date | None = None
    notes: str | None = None


class TransactionResponse(TransactionBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    created_at: datetime
    total_amount: float
    total_amount_krw: float


class TransactionWithStock(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    stock_id: int
    transaction_type: TransactionType
    quantity: float
    price: float
    exchange_rate: float
    fees: float
    transaction_date: date
    notes: str | None
    created_at: datetime
    total_amount: float
    total_amount_krw: float
    stock: StockResponse
    realized_gain: float | None = None
    realized_gain_percent: float | None = None


class TransactionPageResponse(BaseModel):
    content: list[TransactionWithStock]
    total_elements: int
    total_pages: int
    current_page: int
    available_years: list[int]
