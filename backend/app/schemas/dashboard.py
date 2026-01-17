from datetime import date
from pydantic import BaseModel

from app.models.stock import MarketType


class PortfolioSummary(BaseModel):
    total_value_krw: float
    total_invested_krw: float
    total_unrealized_gain: float
    total_unrealized_gain_percent: float
    daily_pnl: float
    daily_pnl_percent: float
    total_dividends: float
    exchange_rate: float


class MarketBreakdown(BaseModel):
    market_type: MarketType
    value_original: float
    value_krw: float
    weight_percent: float
    unrealized_gain: float
    unrealized_gain_percent: float


class DailyPerformancePoint(BaseModel):
    date: date
    total_value_krw: float
    daily_pnl: float
    daily_pnl_percent: float
    cumulative_return_percent: float


class AssetTrendResponse(BaseModel):
    data: list[DailyPerformancePoint]
    period_return_percent: float
    max_drawdown_percent: float


class DailyPnlHistoryItem(BaseModel):
    date: date
    daily_pnl: float
    daily_pnl_percent: float
    total_value_krw: float | None = None  # Optional if filtered by stock
    roi: float = 0.0 # Return on Investment for the day


class DailyPnlHistoryResponse(BaseModel):
    data: list[DailyPnlHistoryItem]
    total_pnl: float
    total_roi_percent: float
    total_count: int = 0
