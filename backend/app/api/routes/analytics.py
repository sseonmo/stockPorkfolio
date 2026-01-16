from typing import Annotated
from datetime import date, timedelta
from decimal import Decimal
from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.daily_performance import DailyPerformance
from app.models.user import User
from app.schemas.analytics import (
    SectorAllocation,
    BenchmarkComparison,
    BenchmarkDataPoint,
    RiskMetrics,
    ConcentrationWarning,
)
from app.api.routes.auth import get_current_user
from app.services.holding_service import holding_service
from app.external.yfinance_client import yfinance_client

router = APIRouter()

CONCENTRATION_THRESHOLD = 20.0


@router.get("/sectors", response_model=list[SectorAllocation])
async def get_sector_allocation(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[dict]:
    holdings = await holding_service.get_holdings_with_metrics(db, current_user.id)

    sector_data: dict[str, dict] = defaultdict(
        lambda: {"value_krw": Decimal("0"), "stock_count": 0}
    )
    total_value = Decimal("0")

    for h in holdings:
        stock = h["stock"]
        if not stock:
            continue
        sector = stock.sector or "Unknown"
        value_krw = Decimal(str(h["current_value_krw"]))
        sector_data[sector]["value_krw"] += value_krw
        sector_data[sector]["stock_count"] += 1
        total_value += value_krw

    result = []
    for sector, data in sorted(sector_data.items(), key=lambda x: x[1]["value_krw"], reverse=True):
        weight = float(data["value_krw"] / total_value * 100) if total_value > 0 else 0
        result.append({
            "sector": sector,
            "value_krw": float(data["value_krw"]),
            "weight_percent": weight,
            "stock_count": data["stock_count"],
        })

    return result


@router.get("/benchmark", response_model=BenchmarkComparison)
async def get_benchmark_comparison(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    benchmark: Annotated[str, Query()] = "SP500",
    days: Annotated[int, Query(ge=30, le=365)] = 90,
) -> dict:
    benchmark_tickers = {
        "KOSPI": ("^KS11", "KOSPI"),
        "SP500": ("^GSPC", "S&P 500"),
        "NASDAQ": ("^IXIC", "NASDAQ"),
    }
    
    ticker, name = benchmark_tickers.get(benchmark, ("^GSPC", "S&P 500"))
    start_date = date.today() - timedelta(days=days)

    stmt = (
        select(DailyPerformance)
        .where(
            DailyPerformance.user_id == current_user.id,
            DailyPerformance.record_date >= start_date,
        )
        .order_by(DailyPerformance.record_date)
    )
    result = await db.execute(stmt)
    performances = list(result.scalars().all())

    benchmark_data = await yfinance_client.get_benchmark_data(
        benchmark, start_date, date.today()
    )

    benchmark_by_date = {d["date"]: d["close"] for d in benchmark_data}

    data = []
    portfolio_base = performances[0].total_value_krw if performances else 0
    benchmark_base = benchmark_data[0]["close"] if benchmark_data else 0

    for p in performances:
        benchmark_close = benchmark_by_date.get(p.record_date)
        if benchmark_close is None:
            continue

        portfolio_return = (
            float((p.total_value_krw - portfolio_base) / portfolio_base * 100)
            if portfolio_base > 0 else 0
        )
        benchmark_return = (
            float((benchmark_close - benchmark_base) / benchmark_base * 100)
            if benchmark_base > 0 else 0
        )

        data.append({
            "date": p.record_date,
            "portfolio_return_percent": portfolio_return,
            "benchmark_return_percent": benchmark_return,
        })

    portfolio_total = data[-1]["portfolio_return_percent"] if data else 0
    benchmark_total = data[-1]["benchmark_return_percent"] if data else 0

    return {
        "benchmark_name": name,
        "benchmark_ticker": ticker,
        "data": data,
        "portfolio_total_return": portfolio_total,
        "benchmark_total_return": benchmark_total,
        "alpha": portfolio_total - benchmark_total,
    }


@router.get("/risk", response_model=RiskMetrics)
async def get_risk_metrics(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    days: Annotated[int, Query(ge=30, le=365)] = 90,
) -> dict:
    holdings = await holding_service.get_holdings_with_metrics(db, current_user.id)

    warnings = []
    sorted_holdings = sorted(holdings, key=lambda h: h["weight_percent"], reverse=True)

    for h in sorted_holdings:
        if h["weight_percent"] >= CONCENTRATION_THRESHOLD:
            stock = h["stock"]
            if stock:
                warnings.append({
                    "ticker": stock.ticker,
                    "name": stock.name,
                    "weight_percent": h["weight_percent"],
                    "threshold_percent": CONCENTRATION_THRESHOLD,
                    "message": f"{stock.ticker} is {h['weight_percent']:.1f}% of portfolio (threshold: {CONCENTRATION_THRESHOLD}%)",
                })

    top_5_weight = sum(h["weight_percent"] for h in sorted_holdings[:5])

    unique_sectors = len(set(h["stock"].sector for h in holdings if h["stock"] and h["stock"].sector))
    total_stocks = len(holdings)
    diversification_score = min(100, (unique_sectors * 10) + (total_stocks * 5))

    start_date = date.today() - timedelta(days=days)
    stmt = (
        select(DailyPerformance)
        .where(
            DailyPerformance.user_id == current_user.id,
            DailyPerformance.record_date >= start_date,
        )
        .order_by(DailyPerformance.record_date)
    )
    result = await db.execute(stmt)
    performances = list(result.scalars().all())

    max_drawdown = Decimal("0")
    max_drawdown_start = None
    max_drawdown_end = None
    peak_value = Decimal("0")
    peak_date = None
    current_drawdown_start = None

    for p in performances:
        value = Decimal(str(p.total_value_krw))
        if value >= peak_value:
            peak_value = value
            peak_date = p.record_date
            current_drawdown_start = p.record_date
        else:
            if peak_value > 0:
                drawdown = (peak_value - value) / peak_value * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                    max_drawdown_start = current_drawdown_start
                    max_drawdown_end = p.record_date

    return {
        "max_drawdown_percent": float(max_drawdown),
        "max_drawdown_start": max_drawdown_start,
        "max_drawdown_end": max_drawdown_end,
        "concentration_warnings": warnings,
        "top_5_weight_percent": top_5_weight,
        "diversification_score": diversification_score,
    }
