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
from app.external.kis_client import kis_client
from app.external.yfinance_client import yfinance_client


async def _update_kr_prices():
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
            today = date.today()
            for stock in stocks:
                price_data = await kis_client.get_stock_price(stock.ticker)
                if price_data and price_data.get("current_price"):
                    stock.current_price = price_data["current_price"]
                    
                    existing_stmt = select(MarketDataHistory).where(
                        MarketDataHistory.stock_id == stock.id,
                        MarketDataHistory.record_date == today,
                    )
                    existing_result = await db.execute(existing_stmt)
                    existing = existing_result.scalar_one_or_none()
                    
                    if existing:
                        existing.close_price = price_data["current_price"]
                    else:
                        market_data = MarketDataHistory(
                            stock_id=stock.id,
                            record_date=today,
                            close_price=price_data["current_price"],
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


async def _update_us_prices():
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
            today = date.today()
            for stock in stocks:
                info = await yfinance_client.get_stock_info(stock.ticker)
                if info and info.get("current_price"):
                    stock.current_price = info["current_price"]
                    
                    existing_stmt = select(MarketDataHistory).where(
                        MarketDataHistory.stock_id == stock.id,
                        MarketDataHistory.record_date == today,
                    )
                    existing_result = await db.execute(existing_stmt)
                    existing = existing_result.scalar_one_or_none()
                    
                    if existing:
                        existing.close_price = info["current_price"]
                    else:
                        market_data = MarketDataHistory(
                            stock_id=stock.id,
                            record_date=today,
                            close_price=info["current_price"],
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


async def _create_daily_snapshot():
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
            today = date.today()

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
                        DailyPerformance.record_date < today,
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
                    DailyPerformance.record_date == today,
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
                        record_date=today,
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


@celery_app.task(name="app.tasks.batch_tasks.refresh_kis_token")
def refresh_kis_token():
    async def _refresh():
        await kis_client._get_access_token()
    asyncio.run(_refresh())
    return {"status": "success", "task": "refresh_kis_token"}
