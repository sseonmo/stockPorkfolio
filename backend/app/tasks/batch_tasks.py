import asyncio
from datetime import datetime, date
from decimal import Decimal
import json

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.celery_app import celery_app
from app.core.database import get_db_context
from app.models.stock import Stock, MarketType
from app.models.holding import Holding
from app.models.daily_performance import DailyPerformance
from app.models.market_data import MarketDataHistory
from app.models.batch_job import BatchJobStatus, JobStatus
from app.models.stock_daily_performance import StockDailyPerformance
from app.external.kis_client import kis_client
from app.external.yfinance_client import yfinance_client


async def _update_kr_prices(target_date: date | None = None):
    target = target_date or date.today()
    async with get_db_context() as db:
        job = BatchJobStatus(
            job_name="update_kr_stock_prices",
            status=JobStatus.RUNNING,
        )
        db.add(job)
        await db.flush()

        try:
            stmt = select(Stock).where(Stock.market_type == MarketType.KR)
            result = await db.execute(stmt)
            stocks = result.scalars().all()

            processed = 0
            for stock in stocks:
                price_data = await kis_client.get_stock_price(stock.ticker)
                if price_data and price_data.get("current_price"):
                    stock.current_price = price_data["current_price"]
                    
                    existing_stmt = select(MarketDataHistory).where(
                        MarketDataHistory.stock_id == stock.id,
                        MarketDataHistory.record_date == target,
                    )
                    existing_result = await db.execute(existing_stmt)
                    existing = existing_result.scalar_one_or_none()
                    
                    if existing:
                        existing.open_price = price_data.get("open_price")
                        existing.high_price = price_data.get("high_price")
                        existing.low_price = price_data.get("low_price")
                        existing.close_price = price_data["current_price"]
                        existing.volume = price_data.get("volume")
                    else:
                        market_data = MarketDataHistory(
                            stock_id=stock.id,
                            record_date=target,
                            open_price=price_data.get("open_price"),
                            high_price=price_data.get("high_price"),
                            low_price=price_data.get("low_price"),
                            close_price=price_data["current_price"],
                            volume=price_data.get("volume"),
                        )
                        db.add(market_data)
                    processed += 1

            job.status = JobStatus.SUCCESS
            job.completed_at = datetime.utcnow()
            job.records_processed = processed
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error_message = str(e)
            raise
    
    await _calculate_stock_daily_pnl(target)
    await _create_daily_snapshot(target)


async def _update_us_prices(target_date: date | None = None):
    target = target_date or date.today()
    async with get_db_context() as db:
        job = BatchJobStatus(
            job_name="update_us_stock_prices",
            status=JobStatus.RUNNING,
        )
        db.add(job)
        await db.flush()

        try:
            stmt = select(Stock).where(Stock.market_type == MarketType.US)
            result = await db.execute(stmt)
            stocks = result.scalars().all()

            processed = 0
            for stock in stocks:
                info = await yfinance_client.get_stock_info(stock.ticker)
                if info and info.get("current_price"):
                    stock.current_price = info["current_price"]
                    
                    existing_stmt = select(MarketDataHistory).where(
                        MarketDataHistory.stock_id == stock.id,
                        MarketDataHistory.record_date == target,
                    )
                    existing_result = await db.execute(existing_stmt)
                    existing = existing_result.scalar_one_or_none()
                    
                    if existing:
                        existing.open_price = info.get("open_price")
                        existing.high_price = info.get("high_price")
                        existing.low_price = info.get("low_price")
                        existing.close_price = info["current_price"]
                        existing.volume = info.get("volume")
                    else:
                        market_data = MarketDataHistory(
                            stock_id=stock.id,
                            record_date=target,
                            open_price=info.get("open_price"),
                            high_price=info.get("high_price"),
                            low_price=info.get("low_price"),
                            close_price=info["current_price"],
                            volume=info.get("volume"),
                        )
                        db.add(market_data)
                    processed += 1

            job.status = JobStatus.SUCCESS
            job.completed_at = datetime.utcnow()
            job.records_processed = processed
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error_message = str(e)
            raise
    
    await _calculate_stock_daily_pnl(target)
    await _create_daily_snapshot(target)


async def _create_daily_snapshot(target_date: date | None = None):
    target = target_date or date.today()
    async with get_db_context() as db:
        job = BatchJobStatus(
            job_name="create_daily_performance_snapshot",
            status=JobStatus.RUNNING,
        )
        db.add(job)
        await db.flush()

        try:
            exchange_rate = await yfinance_client.get_exchange_rate()

            stmt = (
                select(Holding)
                .options(selectinload(Holding.stock))
                .distinct(Holding.user_id)
            )
            result = await db.execute(stmt)
            user_ids = list(set(h.user_id for h in result.scalars().all()))

            processed = 0

            for user_id in user_ids:
                stmt = (
                    select(Holding)
                    .options(selectinload(Holding.stock))
                    .where(Holding.user_id == user_id)
                )
                result = await db.execute(stmt)
                holdings = result.scalars().all()

                total_value_krw = Decimal("0")
                total_invested_krw = Decimal("0")
                kr_value = Decimal("0")
                us_value_usd = Decimal("0")
                us_value_krw = Decimal("0")
                total_dividends = Decimal("0")

                for h in holdings:
                    if not h.stock:
                        continue
                    
                    price = h.stock.current_price or h.average_cost
                    value = Decimal(str(h.quantity)) * Decimal(str(price))
                    
                    if h.stock.market_type == MarketType.KR:
                        kr_value += value
                        total_value_krw += value
                    else:
                        us_value_usd += value
                        value_krw = value * Decimal(str(exchange_rate))
                        us_value_krw += value_krw
                        total_value_krw += value_krw
                    
                    total_invested_krw += Decimal(str(h.total_invested))
                    total_dividends += Decimal(str(h.total_dividends))

                yesterday_stmt = (
                    select(DailyPerformance)
                    .where(
                        DailyPerformance.user_id == user_id,
                        DailyPerformance.record_date < target,
                    )
                    .order_by(DailyPerformance.record_date.desc())
                    .limit(1)
                )
                yesterday_result = await db.execute(yesterday_stmt)
                yesterday = yesterday_result.scalar_one_or_none()

                daily_pnl = Decimal("0")
                daily_pnl_pct = Decimal("0")
                cumulative_return = total_value_krw - total_invested_krw
                cumulative_return_pct = (
                    cumulative_return / total_invested_krw * 100
                    if total_invested_krw > 0 else Decimal("0")
                )

                if yesterday:
                    daily_pnl = total_value_krw - Decimal(str(yesterday.total_value_krw))
                    if yesterday.total_value_krw > 0:
                        daily_pnl_pct = daily_pnl / Decimal(str(yesterday.total_value_krw)) * 100

                existing_perf_stmt = select(DailyPerformance).where(
                    DailyPerformance.user_id == user_id,
                    DailyPerformance.record_date == target,
                )
                existing_perf_result = await db.execute(existing_perf_stmt)
                existing_perf = existing_perf_result.scalar_one_or_none()

                if existing_perf:
                    existing_perf.total_value_krw = float(total_value_krw)
                    existing_perf.total_invested_krw = float(total_invested_krw)
                    existing_perf.kr_value = float(kr_value)
                    existing_perf.us_value_usd = float(us_value_usd)
                    existing_perf.us_value_krw = float(us_value_krw)
                    existing_perf.exchange_rate = exchange_rate
                    existing_perf.daily_pnl = float(daily_pnl)
                    existing_perf.daily_pnl_percent = float(daily_pnl_pct)
                    existing_perf.cumulative_return = float(cumulative_return)
                    existing_perf.cumulative_return_percent = float(cumulative_return_pct)
                    existing_perf.total_dividends = float(total_dividends)
                else:
                    perf = DailyPerformance(
                        user_id=user_id,
                        record_date=target,
                        total_value_krw=float(total_value_krw),
                        total_invested_krw=float(total_invested_krw),
                        kr_value=float(kr_value),
                        us_value_usd=float(us_value_usd),
                        us_value_krw=float(us_value_krw),
                        exchange_rate=exchange_rate,
                        daily_pnl=float(daily_pnl),
                        daily_pnl_percent=float(daily_pnl_pct),
                        cumulative_return=float(cumulative_return),
                        cumulative_return_percent=float(cumulative_return_pct),
                        total_dividends=float(total_dividends),
                    )
                    db.add(perf)
                processed += 1

            job.status = JobStatus.SUCCESS
            job.completed_at = datetime.utcnow()
            job.records_processed = processed

        except Exception as e:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error_message = str(e)
            raise


@celery_app.task(
    bind=True,
    name="app.tasks.batch_tasks.update_kr_stock_prices",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def update_kr_stock_prices(self):
    asyncio.run(_update_kr_prices())
    return {"status": "success", "task": "update_kr_stock_prices"}


@celery_app.task(
    bind=True,
    name="app.tasks.batch_tasks.update_us_stock_prices",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def update_us_stock_prices(self):
    asyncio.run(_update_us_prices())
    return {"status": "success", "task": "update_us_stock_prices"}


@celery_app.task(
    bind=True,
    name="app.tasks.batch_tasks.create_daily_performance_snapshot",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def create_daily_performance_snapshot(self):
    asyncio.run(_create_daily_snapshot())
    return {"status": "success", "task": "create_daily_performance_snapshot"}


async def _calculate_stock_daily_pnl(target_date: date | None = None):
    target = target_date or date.today()
    async with get_db_context() as db:
        job = BatchJobStatus(
            job_name="calculate_stock_daily_pnl",
            status=JobStatus.RUNNING,
        )
        db.add(job)
        await db.flush()

        try:
            processed = 0

            stmt = select(Holding).options(selectinload(Holding.stock))
            result = await db.execute(stmt)
            all_holdings = result.scalars().all()
            
            user_ids = set(h.user_id for h in all_holdings)

            for user_id in user_ids:
                user_holdings = [h for h in all_holdings if h.user_id == user_id]
                
                for h in user_holdings:
                    if not h.stock or h.quantity <= 0:
                        continue
                    
                    yesterday_stmt = (
                        select(StockDailyPerformance)
                        .where(
                            StockDailyPerformance.user_id == user_id,
                            StockDailyPerformance.stock_id == h.stock_id,
                            StockDailyPerformance.record_date < target
                        )
                        .order_by(StockDailyPerformance.record_date.desc())
                        .limit(1)
                    )
                    yesterday_result = await db.execute(yesterday_stmt)
                    yesterday_perf = yesterday_result.scalar_one_or_none()
                    
                    close_price = Decimal(str(h.stock.current_price or h.average_cost))
                    prev_close = Decimal(str(yesterday_perf.close_price)) if yesterday_perf else close_price
                    quantity = Decimal(str(h.quantity))
                    
                    daily_pnl = quantity * (close_price - prev_close)
                    daily_pnl_pct = ((close_price - prev_close) / prev_close * 100) if prev_close > 0 else Decimal("0")
                    position_value = quantity * close_price
                    
                    existing_stmt = select(StockDailyPerformance).where(
                        StockDailyPerformance.user_id == user_id,
                        StockDailyPerformance.stock_id == h.stock_id,
                        StockDailyPerformance.record_date == target
                    )
                    existing_result = await db.execute(existing_stmt)
                    existing = existing_result.scalar_one_or_none()
                    
                    if existing:
                        existing.quantity = float(quantity)
                        existing.close_price = float(close_price)
                        existing.prev_close_price = float(prev_close)
                        existing.daily_pnl = float(daily_pnl)
                        existing.daily_pnl_percent = float(daily_pnl_pct)
                        existing.position_value = float(position_value)
                    else:
                        stock_perf = StockDailyPerformance(
                            user_id=user_id,
                            stock_id=h.stock_id,
                            record_date=target,
                            quantity=float(quantity),
                            close_price=float(close_price),
                            prev_close_price=float(prev_close),
                            daily_pnl=float(daily_pnl),
                            daily_pnl_percent=float(daily_pnl_pct),
                            position_value=float(position_value)
                        )
                        db.add(stock_perf)
                    
                    processed += 1

            job.status = JobStatus.SUCCESS
            job.completed_at = datetime.utcnow()
            job.records_processed = processed

        except Exception as e:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error_message = str(e)
            raise


@celery_app.task(name="app.tasks.batch_tasks.refresh_kis_token")
def refresh_kis_token():
    async def _refresh():
        await kis_client._get_access_token()
    asyncio.run(_refresh())
    return {"status": "success", "task": "refresh_kis_token"}


@celery_app.task(
    bind=True,
    name="app.tasks.batch_tasks.calculate_stock_daily_pnl",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def calculate_stock_daily_pnl(self):
    asyncio.run(_calculate_stock_daily_pnl())
    return {"status": "success", "task": "calculate_stock_daily_pnl"}
