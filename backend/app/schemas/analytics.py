from datetime import date
from pydantic import BaseModel


class SectorStock(BaseModel):
    name: str
    ticker: str
    value_krw: float
    weight_percent: float


class SectorAllocation(BaseModel):
    sector: str
    value_krw: float
    weight_percent: float
    stock_count: int
    stocks: list[SectorStock]


class BenchmarkDataPoint(BaseModel):
    date: date
    portfolio_return_percent: float
    benchmark_return_percent: float


class BenchmarkComparison(BaseModel):
    benchmark_name: str
    benchmark_ticker: str
    data: list[BenchmarkDataPoint]
    portfolio_total_return: float
    benchmark_total_return: float
    alpha: float


class ConcentrationWarning(BaseModel):
    ticker: str
    name: str
    weight_percent: float
    threshold_percent: float
    message: str


class RiskMetrics(BaseModel):
    max_drawdown_percent: float
    max_drawdown_start: date | None
    max_drawdown_end: date | None
    concentration_warnings: list[ConcentrationWarning]
    top_5_weight_percent: float
    diversification_score: float


class MonthlyReturn(BaseModel):
    year: int
    month: int
    return_percent: float
    starting_value: float
    ending_value: float


class PeriodReturns(BaseModel):
    one_month: float
    three_months: float
    six_months: float
    one_year: float
    ytd: float


class WinLossStats(BaseModel):
    total_days: int
    up_days: int
    down_days: int
    flat_days: int
    win_rate: float
    avg_win_percent: float
    avg_loss_percent: float
    best_day: date | None
    best_day_return: float
    worst_day: date | None
    worst_day_return: float
    profit_factor: float
