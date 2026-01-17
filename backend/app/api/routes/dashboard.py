from typing import Annotated
from datetime import date, timedelta
from decimal import Decimal
from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.daily_performance import DailyPerformance
from app.models.stock import MarketType
from app.models.user import User
from app.models.dividend import Dividend
from app.schemas.dashboard import (
    PortfolioSummary,
    MarketBreakdown,
    DailyPerformancePoint,
    AssetTrendResponse,
)
from app.api.routes.auth import get_current_user
from app.services.holding_service import holding_service
from app.external.yfinance_client import yfinance_client
from app.external.kis_client import kis_client
from sqlalchemy.orm import selectinload

router = APIRouter()


@router.get("/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    exchange_rate = await yfinance_client.get_exchange_rate()
    holdings = await holding_service.get_holdings_with_metrics(
        db, current_user.id, exchange_rate
    )

    total_value_krw = Decimal("0")
    total_invested_krw = Decimal("0")
    total_dividends = Decimal("0")

    for h in holdings:
        total_value_krw += Decimal(str(h["current_value_krw"]))
        total_invested_krw += Decimal(str(h["total_invested"]))
        total_dividends += Decimal(str(h["total_dividends"]))

    total_unrealized_gain = total_value_krw - total_invested_krw
    total_unrealized_gain_pct = (
        float(total_unrealized_gain / total_invested_krw * 100)
        if total_invested_krw > 0 else 0.0
    )

    yesterday = date.today() - timedelta(days=1)
    stmt = (
        select(DailyPerformance)
        .where(
            DailyPerformance.user_id == current_user.id,
            DailyPerformance.record_date == yesterday,
        )
    )
    result = await db.execute(stmt)
    yesterday_perf = result.scalar_one_or_none()

    daily_pnl = float(total_value_krw) - (float(yesterday_perf.total_value_krw) if yesterday_perf else float(total_invested_krw))
    daily_pnl_pct = (
        (daily_pnl / float(yesterday_perf.total_value_krw) * 100)
        if yesterday_perf and yesterday_perf.total_value_krw > 0
        else 0.0
    )

    return {
        "total_value_krw": float(total_value_krw),
        "total_invested_krw": float(total_invested_krw),
        "total_unrealized_gain": float(total_unrealized_gain),
        "total_unrealized_gain_percent": total_unrealized_gain_pct,
        "daily_pnl": daily_pnl,
        "daily_pnl_percent": daily_pnl_pct,
        "total_dividends": float(total_dividends),
        "exchange_rate": exchange_rate,
    }


@router.get("/market-breakdown", response_model=list[MarketBreakdown])
async def get_market_breakdown(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[dict]:
    exchange_rate = await yfinance_client.get_exchange_rate()
    holdings = await holding_service.get_holdings_with_metrics(
        db, current_user.id, exchange_rate
    )

    kr_value = Decimal("0")
    kr_invested = Decimal("0")
    us_value_usd = Decimal("0")
    us_value_krw = Decimal("0")
    us_invested = Decimal("0")
    total_value_krw = Decimal("0")

    for h in holdings:
        stock = h["stock"]
        if not stock:
            continue
        
        value_krw = Decimal(str(h["current_value_krw"]))
        total_value_krw += value_krw
        
        if stock.market_type == MarketType.KR:
            kr_value += value_krw
            kr_invested += Decimal(str(h["total_invested"]))
        else:
            us_value_krw += value_krw
            us_value_usd += Decimal(str(h["current_value"]))
            us_invested += Decimal(str(h["total_invested"]))

    result = []
    
    if kr_value > 0:
        kr_gain = kr_value - kr_invested
        result.append({
            "market_type": MarketType.KR,
            "value_original": float(kr_value),
            "value_krw": float(kr_value),
            "weight_percent": float(kr_value / total_value_krw * 100) if total_value_krw > 0 else 0,
            "unrealized_gain": float(kr_gain),
            "unrealized_gain_percent": float(kr_gain / kr_invested * 100) if kr_invested > 0 else 0,
        })

    if us_value_krw > 0:
        us_gain = us_value_krw - us_invested
        result.append({
            "market_type": MarketType.US,
            "value_original": float(us_value_usd),
            "value_krw": float(us_value_krw),
            "weight_percent": float(us_value_krw / total_value_krw * 100) if total_value_krw > 0 else 0,
            "unrealized_gain": float(us_gain),
            "unrealized_gain_percent": float(us_gain / us_invested * 100) if us_invested > 0 else 0,
        })

    return result


@router.get("/trend", response_model=AssetTrendResponse)
async def get_asset_trend(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
    stock_ids: Annotated[list[int] | None, Query()] = None,
) -> dict:
    from app.models.holding import Holding
    from app.models.market_data import MarketDataHistory
    
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=7)

    data = []
    peak_value = Decimal("0")
    max_drawdown = Decimal("0")

    if not stock_ids:
        stmt = (
            select(DailyPerformance)
            .where(
                DailyPerformance.user_id == current_user.id,
                DailyPerformance.record_date >= start_date,
                DailyPerformance.record_date <= end_date,
            )
            .order_by(DailyPerformance.record_date)
        )
        result = await db.execute(stmt)
        performances = result.scalars().all()

        for p in performances:
            data.append({
                "date": p.record_date,
                "total_value_krw": float(p.total_value_krw),
                "daily_pnl": float(p.daily_pnl),
                "daily_pnl_percent": float(p.daily_pnl_percent),
                "cumulative_return_percent": float(p.cumulative_return_percent),
            })
            
            value = Decimal(str(p.total_value_krw))
            if value > peak_value:
                peak_value = value
            if peak_value > 0:
                drawdown = (peak_value - value) / peak_value * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
    else:
        holdings_stmt = (
            select(Holding)
            .options(selectinload(Holding.stock))
            .where(
                Holding.user_id == current_user.id,
                Holding.stock_id.in_(stock_ids)
            )
        )
        holdings_result = await db.execute(holdings_stmt)
        holdings = {h.stock_id: h for h in holdings_result.scalars().all()}
        
        if holdings:
            exchange_rate = await yfinance_client.get_exchange_rate()
            
            market_data_stmt = (
                select(MarketDataHistory)
                .where(
                    MarketDataHistory.stock_id.in_(stock_ids),
                    MarketDataHistory.record_date >= start_date,
                    MarketDataHistory.record_date <= end_date,
                )
                .order_by(MarketDataHistory.record_date)
            )
            market_result = await db.execute(market_data_stmt)
            market_data = market_result.scalars().all()
            
            date_values: dict[date, Decimal] = {}
            for md in market_data:
                h = holdings.get(md.stock_id)
                if not h or not h.stock:
                    continue
                
                value = Decimal(str(h.quantity)) * Decimal(str(md.close_price))
                if h.stock.market_type == MarketType.US:
                    value = value * Decimal(str(exchange_rate))
                
                if md.record_date not in date_values:
                    date_values[md.record_date] = Decimal("0")
                date_values[md.record_date] += value
            
            total_invested = sum(Decimal(str(h.total_invested)) for h in holdings.values())
            prev_value = None
            
            for d in sorted(date_values.keys()):
                value = date_values[d]
                daily_pnl = float(value - prev_value) if prev_value else 0.0
                daily_pnl_pct = (daily_pnl / float(prev_value) * 100) if prev_value and prev_value > 0 else 0.0
                cumulative_return_pct = float((value - total_invested) / total_invested * 100) if total_invested > 0 else 0.0
                
                data.append({
                    "date": d,
                    "total_value_krw": float(value),
                    "daily_pnl": daily_pnl,
                    "daily_pnl_percent": daily_pnl_pct,
                    "cumulative_return_percent": cumulative_return_pct,
                })
                
                if value > peak_value:
                    peak_value = value
                if peak_value > 0:
                    drawdown = (peak_value - value) / peak_value * 100
                    if drawdown > max_drawdown:
                        max_drawdown = drawdown
                
                prev_value = value

    period_return = 0.0
    if len(data) >= 2:
        first_value = data[0]["total_value_krw"]
        last_value = data[-1]["total_value_krw"]
        if first_value > 0:
            period_return = float((last_value - first_value) / first_value * 100)

    return {
        "data": data,
        "period_return_percent": period_return,
        "max_drawdown_percent": float(max_drawdown),
    }


from app.schemas.dashboard import DailyPnlHistoryResponse, DailyPnlHistoryItem

@router.get("/daily-pnl", response_model=DailyPnlHistoryResponse)
async def get_daily_pnl_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
    stock_ids: Annotated[list[int] | None, Query()] = None,
    skip: int = 0,
    limit: int = 20,
) -> dict:
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()

    data_points = []
    
    # Pre-fetch exchange rate once
    exchange_rate = await yfinance_client.get_exchange_rate()

    if not stock_ids:
        stmt = (
            select(DailyPerformance)
            .where(
                DailyPerformance.user_id == current_user.id,
                DailyPerformance.record_date >= start_date,
                DailyPerformance.record_date <= end_date,
            )
            .order_by(DailyPerformance.record_date)
        )
        result = await db.execute(stmt)
        performances = result.scalars().all()

        if not performances:
            return {
                "data": [],
                "total_pnl": 0.0,
                "total_roi_percent": 0.0,
                "total_count": 0
            }

        prev_value = None
        for p in performances:
            daily_pnl = float(p.daily_pnl)
            daily_pnl_pct = float(p.daily_pnl_percent)
            
            if daily_pnl == 0 and prev_value is not None:
                daily_pnl = float(p.total_value_krw) - prev_value
                if prev_value > 0:
                    daily_pnl_pct = (daily_pnl / prev_value) * 100
            
            data_points.append({
                "date": p.record_date,
                "daily_pnl": daily_pnl,
                "daily_pnl_percent": daily_pnl_pct,
                "total_value_krw": float(p.total_value_krw),
                "roi": daily_pnl_pct,
            })
            prev_value = float(p.total_value_krw)
    
    else:
        from app.models.stock_daily_performance import StockDailyPerformance
        
        stmt = (
            select(StockDailyPerformance)
            .where(
                StockDailyPerformance.user_id == current_user.id,
                StockDailyPerformance.stock_id.in_(stock_ids),
                StockDailyPerformance.record_date >= start_date,
                StockDailyPerformance.record_date <= end_date,
            )
            .order_by(StockDailyPerformance.record_date)
        )
        result = await db.execute(stmt)
        stock_perfs = result.scalars().all()
        
        daily_data = defaultdict(lambda: {"daily_pnl": Decimal("0"), "position_value": Decimal("0")})
        
        for sp in stock_perfs:
            daily_data[sp.record_date]["daily_pnl"] += Decimal(str(sp.daily_pnl))
            daily_data[sp.record_date]["position_value"] += Decimal(str(sp.position_value))
        
        for record_date, values in sorted(daily_data.items()):
            daily_pnl = values["daily_pnl"]
            position_value = values["position_value"]
            
            prev_value = position_value - daily_pnl
            roi = 0.0
            if prev_value > 0:
                roi = float(daily_pnl / prev_value * 100)
            
            data_points.append({
                "date": record_date,
                "daily_pnl": float(daily_pnl),
                "daily_pnl_percent": roi,
                "total_value_krw": float(position_value),
                "roi": roi
            })

    total_count = len(data_points)
    total_pnl = sum(d["daily_pnl"] for d in data_points)
    
    # 기간 수익률 계산: 첫날 자산가치 기준
    total_roi = 0.0
    if data_points:
        first_day_value = data_points[0].get("total_value_krw", 0)
        if first_day_value:
            # 첫날 자산가치에서 첫날 손익을 빼면 시작 자산
            first_day_pnl = data_points[0].get("daily_pnl", 0)
            initial_value = first_day_value - first_day_pnl
            if initial_value > 0:
                total_roi = (total_pnl / initial_value) * 100

    # 최신 날짜가 먼저 나오도록 정렬 (내림차순)
    data_points.sort(key=lambda x: x["date"], reverse=True)

    # 페이징 적용
    paged_data = data_points[skip : skip + limit]

    return {
        "data": paged_data,
        "total_pnl": total_pnl,
        "total_roi_percent": total_roi,
        "total_count": total_count
    }


@router.get("/dividend-trend")
async def get_dividend_trend(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
    stock_ids: Annotated[list[int] | None, Query()] = None,
) -> dict:
    if not end_date:
        end_date = date.today()
    if not start_date:
        # 기본 1년 전부터
        start_date = end_date - timedelta(days=365)

    # 1. 시작일 이전의 누적 배당금 계산 (Base Amount)
    base_query = (
        select(Dividend)
        .where(
            Dividend.user_id == current_user.id,
            Dividend.dividend_date < start_date
        )
    )
    if stock_ids:
        base_query = base_query.where(Dividend.stock_id.in_(stock_ids))
    
    base_result = await db.execute(base_query)
    base_dividends = base_result.scalars().all()
    cumulative_amount = sum(float(d.amount) for d in base_dividends) # 세전 기준

    # 2. 기간 내 배당금 조회
    period_query = (
        select(Dividend)
        .where(
            Dividend.user_id == current_user.id,
            Dividend.dividend_date >= start_date,
            Dividend.dividend_date <= end_date
        )
        .order_by(Dividend.dividend_date)
    )
    if stock_ids:
        period_query = period_query.where(Dividend.stock_id.in_(stock_ids))
        
    period_result = await db.execute(period_query)
    period_dividends = period_result.scalars().all()
    
    # 3. 데이터 포인트 생성
    # 날짜별로 그룹화 필요
    from collections import defaultdict
    div_by_date = defaultdict(float)
    for d in period_dividends:
        div_by_date[d.dividend_date] += float(d.amount)
        
    data = []
    
    # 시작일부터 종료일까지 매일매일 데이터 포인트 생성 (그래프를 위해)
    # 데이터가 없는 날은 이전 누적값 유지 (계단식 상승)
    
    curr = start_date
    while curr <= end_date:
        if curr in div_by_date:
            cumulative_amount += div_by_date[curr]
            
        data.append({
            "date": curr,
            "cumulative_dividend": cumulative_amount,
            "daily_dividend": div_by_date.get(curr, 0.0)
        })
        curr += timedelta(days=1)
        
    return {
        "data": data,
        "total_dividend": cumulative_amount
    }
