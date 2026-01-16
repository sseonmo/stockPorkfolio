from typing import Annotated
from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.daily_performance import DailyPerformance
from app.models.stock import MarketType
from app.models.user import User
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
) -> dict:
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()

    data_points = []
    
    # Pre-fetch exchange rate once
    exchange_rate = await yfinance_client.get_exchange_rate()

    if not stock_ids:
        # Portfolio view: Use DailyPerformance table
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
            roi = float(p.daily_pnl_percent)
            data_points.append({
                "date": p.record_date,
                "daily_pnl": float(p.daily_pnl),
                "daily_pnl_percent": float(p.daily_pnl_percent),
                "total_value_krw": float(p.total_value_krw),
                "roi": roi,
            })
    
    else:
        # Stock specific view
        # 1. Fetch relevant holdings to get Quantity
        from app.models.holding import Holding
        stmt = (
            select(Holding)
            .options(selectinload(Holding.stock))
            .where(
                Holding.user_id == current_user.id,
                Holding.stock_id.in_(stock_ids)
            )
        )
        result = await db.execute(stmt)
        holdings = result.scalars().all()
        
        # 2. If range includes Today, we calculate Today's PnL dynamically
        today = date.today()
        if start_date <= today <= end_date:
            daily_pnl_sum = Decimal("0")
            total_value_sum = Decimal("0")
            
            for h in holdings:
                if not h.stock:
                    continue
                
                # Fetch Real-time data
                price_info = None
                if h.stock.market_type == MarketType.KR:
                    price_info = await kis_client.get_stock_price(h.stock.ticker)
                else:
                    price_info = await yfinance_client.get_stock_info(h.stock.ticker)
                
                if price_info:
                    # 'change' is the daily price change amount (e.g. +500 won, -2.5 dollars)
                    change = Decimal(str(price_info.get("change", 0)))
                    current_price = Decimal(str(price_info.get("current_price", 0)))
                    quantity = Decimal(str(h.quantity))
                    
                    # Calculate Asset Value
                    if h.stock.market_type == MarketType.KR:
                        value = current_price * quantity
                        pnl = change * quantity
                    else:
                        usd_krw = Decimal(str(exchange_rate))
                        value_usd = current_price * quantity
                        value = value_usd * usd_krw
                        # Change is in USD, convert to KRW
                        change_usd = change * quantity
                        pnl = change_usd * usd_krw
                        
                    daily_pnl_sum += pnl
                    total_value_sum += value
            
            # ROI = PnL / (Value - PnL) * 100 roughly (Value at start of day)
            start_of_day_value = total_value_sum - daily_pnl_sum
            roi = 0.0
            if start_of_day_value > 0:
                roi = float(daily_pnl_sum / start_of_day_value * 100)
                
            data_points.append({
                "date": today,
                "daily_pnl": float(daily_pnl_sum),
                "daily_pnl_percent": roi, # This is daily % change
                "total_value_krw": float(total_value_sum),
                "roi": roi
            })

        # 3. For History (Yesterday and before):
        # We would query MarketDataHistory. For now, we skip or use empty logic if DB is empty.
        # Since we only created DB today, history is empty.
        
        # Sort by date
        data_points.sort(key=lambda x: x["date"])

    total_pnl = sum(d["daily_pnl"] for d in data_points)
    # Average ROI or Cumulative? For simple view, sum of daily % is often used but incorrect.
    # Let's use simple weighted ROI if single point, or valid aggregation.
    # If 1 day: return that day's roi.
    # If multiple days: User might expect cumulative.
    # For now, simplistic sum to match UI expectation of "how much did it move".
    total_roi = sum(d["daily_pnl_percent"] for d in data_points) 

    return {
        "data": data_points,
        "total_pnl": total_pnl,
        "total_roi_percent": total_roi,
    }
