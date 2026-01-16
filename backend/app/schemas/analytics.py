from datetime import date
from pydantic import BaseModel


class SectorAllocation(BaseModel):
    sector: str
    value_krw: float
    weight_percent: float
    stock_count: int


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
