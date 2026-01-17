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
    MonthlyReturn,
    WinLossStats,
    PeriodReturns,
)
from app.api.routes.auth import get_current_user
from app.services.holding_service import holding_service
from app.external.yfinance_client import yfinance_client

router = APIRouter()

CONCENTRATION_THRESHOLD = 20.0


@router.get("/period-returns", response_model=PeriodReturns)
async def get_period_returns(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    today = date.today()
    periods = {
        "one_month": today - timedelta(days=30),
        "three_months": today - timedelta(days=90),
        "six_months": today - timedelta(days=180),
        "one_year": today - timedelta(days=365),
        "ytd": date(today.year, 1, 1),
    }
    
    # 가장 오래된 날짜 찾기
    min_date = min(periods.values())
    
    stmt = (
        select(DailyPerformance)
        .where(
            DailyPerformance.user_id == current_user.id,
            DailyPerformance.record_date >= min_date,
        )
        .order_by(DailyPerformance.record_date)
    )
    result = await db.execute(stmt)
    performances = list(result.scalars().all())
    
    if not performances:
        return {k: 0.0 for k in periods.keys()}
        
    perf_map = {p.record_date: p for p in performances}
    latest = performances[-1]
    
    # 최신 데이터의 누적 수익률이 아닌, 해당 기간 동안의 수익률 계산
    # (End - Start) / Start
    
    returns = {}
    
    for key, start_date in periods.items():
        start_perf = None
        for p in performances:
            if p.record_date >= start_date:
                start_perf = p
                break
        
        if not start_perf or start_perf == latest:
            returns[key] = 0.0
            continue
            
        # 기간 수익률 계산: (기말 총자산 - 기초 총자산 - 순입금) / 기초 총자산
        start_val = Decimal(str(start_perf.total_value_krw))
        end_val = Decimal(str(latest.total_value_krw))
        
        invested_diff = Decimal(str(latest.total_invested_krw)) - Decimal(str(start_perf.total_invested_krw))
        dividend_diff = Decimal(str(latest.total_dividends)) - Decimal(str(start_perf.total_dividends))
        
        adjusted_end = end_val + dividend_diff - invested_diff
        
        if start_val > 0:
            ret = float((adjusted_end - start_val) / start_val * 100)
            returns[key] = ret
        else:
            returns[key] = 0.0
            
    return returns


@router.get("/sectors", response_model=list[SectorAllocation])
async def get_sector_allocation(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[dict]:
    holdings = await holding_service.get_holdings_with_metrics(db, current_user.id)

    # 섹터별 데이터 집계
    sector_data: dict[str, dict] = defaultdict(
        lambda: {"value_krw": Decimal("0"), "stocks": []}
    )
    total_value = Decimal("0")

    for h in holdings:
        stock = h["stock"]
        if not stock:
            continue
            
        sector = stock.sector
        if not sector or sector == "Unknown":
            sector = "기타"
            
        value_krw = Decimal(str(h["current_value_krw"]))
        total_value += value_krw
        
        # 타입 힌트를 위해 명시적 형변환 또는 any 사용
        data = sector_data[sector]
        if isinstance(data["value_krw"], Decimal):
            data["value_krw"] += value_krw
            
        if isinstance(data["stocks"], list):
            data["stocks"].append({
                "name": stock.name,
                "ticker": stock.ticker,
                "value_krw": float(value_krw),
                "weight_in_sector": 0.0 
            })

    result = []
    for sector, data in sorted(sector_data.items(), key=lambda x: x[1]["value_krw"], reverse=True):
        # 형변환 안전하게 처리
        sector_val_decimal = data["value_krw"] if isinstance(data["value_krw"], Decimal) else Decimal(str(data["value_krw"]))
        
        weight = float(sector_val_decimal / total_value * 100) if total_value > 0 else 0
        
        stocks_info = []
        raw_stocks = data["stocks"] if isinstance(data["stocks"], list) else []
        
        for s in raw_stocks:
            s_weight = float(Decimal(str(s["value_krw"])) / total_value * 100) if total_value > 0 else 0
            stocks_info.append({
                "name": s["name"],
                "ticker": s["ticker"],
                "value_krw": s["value_krw"],
                "weight_percent": s_weight
            })
        
        stocks_info.sort(key=lambda x: x["value_krw"], reverse=True)
        
        result.append({
            "sector": sector,
            "value_krw": float(sector_val_decimal),
            "weight_percent": weight,
            "stock_count": len(stocks_info),
            "stocks": stocks_info
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


@router.get("/monthly-returns", response_model=list[MonthlyReturn])
async def get_monthly_returns(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[dict]:
    # 모든 기간 데이터 조회
    stmt = (
        select(DailyPerformance)
        .where(DailyPerformance.user_id == current_user.id)
        .order_by(DailyPerformance.record_date)
    )
    result = await db.execute(stmt)
    performances = list(result.scalars().all())
    
    if not performances:
        return []
    
    monthly_data = defaultdict(list)
    for p in performances:
        key = (p.record_date.year, p.record_date.month)
        monthly_data[key].append(p)
    
    results = []
    sorted_months = sorted(monthly_data.keys())
    
    for year, month in sorted_months:
        month_recs = monthly_data[(year, month)]
        month_recs.sort(key=lambda x: x.record_date)
        
        start_rec = month_recs[0]
        end_rec = month_recs[-1]
        
        monthly_pnl = sum(Decimal(str(p.daily_pnl)) for p in month_recs)
        
        # Calculate start value: (Value at start of month) = (First day value) - (First day PnL)
        start_value = Decimal(str(start_rec.total_value_krw)) - Decimal(str(start_rec.daily_pnl))
        
        if start_value <= 0:
            return_pct = 0.0
        else:
            return_pct = float(monthly_pnl / start_value * 100)
            
        results.append({
            "year": year,
            "month": month,
            "return_percent": return_pct,
            "starting_value": float(start_value),
            "ending_value": float(end_rec.total_value_krw)
        })
        
    return results


@router.get("/stats", response_model=WinLossStats)
async def get_trading_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    days: Annotated[int, Query(ge=30, le=365)] = 365,
) -> dict:
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
    
    if not performances:
        return {
            "total_days": 0, "up_days": 0, "down_days": 0, "flat_days": 0,
            "win_rate": 0.0, "avg_win_percent": 0.0, "avg_loss_percent": 0.0,
            "best_day": None, "best_day_return": 0.0,
            "worst_day": None, "worst_day_return": 0.0,
            "profit_factor": 0.0
        }
        
    total_days = len(performances)
    up_days = 0
    down_days = 0
    flat_days = 0
    
    total_win_pct = 0.0
    total_loss_pct = 0.0
    
    gross_profit = 0.0
    gross_loss = 0.0
    
    best_day = None
    best_return = -999.0
    worst_day = None
    worst_return = 999.0
    
    for p in performances:
        pnl = float(p.daily_pnl)
        pnl_pct = float(p.daily_pnl_percent)
        
        if pnl > 0:
            up_days += 1
            total_win_pct += pnl_pct
            gross_profit += pnl
            if pnl_pct > best_return:
                best_return = pnl_pct
                best_day = p.record_date
        elif pnl < 0:
            down_days += 1
            total_loss_pct += pnl_pct
            gross_loss += abs(pnl)
            if pnl_pct < worst_return:
                worst_return = pnl_pct
                worst_day = p.record_date
        else:
            flat_days += 1
            
    win_rate = (up_days / total_days * 100) if total_days > 0 else 0.0
    avg_win = (total_win_pct / up_days) if up_days > 0 else 0.0
    avg_loss = (total_loss_pct / down_days) if down_days > 0 else 0.0
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (999.0 if gross_profit > 0 else 0.0)
    
    return {
        "total_days": total_days,
        "up_days": up_days,
        "down_days": down_days,
        "flat_days": flat_days,
        "win_rate": win_rate,
        "avg_win_percent": avg_win,
        "avg_loss_percent": avg_loss,
        "best_day": best_day,
        "best_day_return": best_return if best_day else 0.0,
        "worst_day": worst_day,
        "worst_day_return": worst_return if worst_day else 0.0,
        "profit_factor": profit_factor,
    }
