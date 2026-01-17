"""
일일 포트폴리오 성과 재계산
- 거래 내역과 시세 데이터를 기반으로 일별 포트폴리오 가치 계산
- daily_performances 테이블 재생성
"""
import asyncio
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from collections import defaultdict

from sqlalchemy import select, delete
from app.core.database import async_session_maker
from app.models.user import User
from app.models.stock import Stock, MarketType
from app.models.transaction import Transaction, TransactionType
from app.models.market_data import MarketDataHistory
from app.models.daily_performance import DailyPerformance
from app.models.dividend import Dividend

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def get_stock_price_on_date(
    session,
    stock_id: int,
    target_date: date,
    price_cache: dict
) -> float:
    """특정 날짜의 종목 종가 조회 (캐시 사용)"""
    cache_key = (stock_id, target_date)
    if cache_key in price_cache:
        return price_cache[cache_key]
    
    stmt = select(MarketDataHistory).where(
        MarketDataHistory.stock_id == stock_id,
        MarketDataHistory.record_date == target_date
    )
    result = await session.execute(stmt)
    market_data = result.scalar_one_or_none()
    
    if market_data:
        price = float(market_data.close_price)
        price_cache[cache_key] = price
        return price
    
    for days_back in range(1, 11):
        past_date = target_date - timedelta(days=days_back)
        stmt = select(MarketDataHistory).where(
            MarketDataHistory.stock_id == stock_id,
            MarketDataHistory.record_date == past_date
        )
        result = await session.execute(stmt)
        market_data = result.scalar_one_or_none()
        
        if market_data:
            price = float(market_data.close_price)
            price_cache[cache_key] = price
            return price
    
    price_cache[cache_key] = 0.0
    return 0.0


async def calculate_daily_performance_for_user(user_id: int):
    """특정 사용자의 일일 포트폴리오 성과 계산"""
    async with async_session_maker() as session:
        logger.info("="*60)
        logger.info(f"사용자 ID {user_id} 일일 성과 계산 시작")
        logger.info("="*60)
        
        stmt = select(Transaction).where(
            Transaction.user_id == user_id
        ).order_by(Transaction.transaction_date)
        result = await session.execute(stmt)
        transactions = result.scalars().all()
        
        if not transactions:
            logger.info("거래 내역이 없습니다.")
            return
        
        first_date = min(tx.transaction_date for tx in transactions)
        last_date = date.today()
        
        logger.info(f"계산 기간: {first_date} ~ {last_date}")
        logger.info(f"총 거래: {len(transactions)}건")
        
        stmt = select(Stock)
        result = await session.execute(stmt)
        stocks = {s.id: s for s in result.scalars().all()}
        
        stmt = select(Dividend).where(Dividend.user_id == user_id)
        result = await session.execute(stmt)
        dividends = result.scalars().all()
        dividends_by_date = defaultdict(Decimal)
        for div in dividends:
            dividends_by_date[div.dividend_date] += Decimal(str(div.amount)) - Decimal(str(div.tax))
        
        logger.info(f"배당 내역: {len(dividends)}건")
        
        await session.execute(
            delete(DailyPerformance).where(DailyPerformance.user_id == user_id)
        )
        await session.commit()
        logger.info("기존 성과 데이터 삭제 완료")
        
        holdings = defaultdict(Decimal)
        total_invested = Decimal("0")
        total_dividends_accumulated = Decimal("0")
        
        tx_by_date = defaultdict(list)
        for tx in transactions:
            tx_by_date[tx.transaction_date].append(tx)
        
        price_cache = {}
        
        current_date = first_date
        saved_count = 0
        
        while current_date <= last_date:
            if current_date in tx_by_date:
                for tx in tx_by_date[current_date]:
                    qty = Decimal(str(tx.quantity))
                    price = Decimal(str(tx.price))
                    exchange_rate = Decimal(str(tx.exchange_rate))
                    fees = Decimal(str(tx.fees))
                    
                    if tx.transaction_type == TransactionType.BUY:
                        holdings[tx.stock_id] += qty
                        amount_krw = qty * price * exchange_rate + fees
                        total_invested += amount_krw
                    elif tx.transaction_type == TransactionType.SELL:
                        holdings[tx.stock_id] -= qty
                        if holdings[tx.stock_id] < 0:
                            holdings[tx.stock_id] = Decimal("0")
                        amount_krw = qty * price * exchange_rate - fees
                        total_invested -= amount_krw
            
            if current_date in dividends_by_date:
                total_dividends_accumulated += dividends_by_date[current_date]
            
            total_value_krw = Decimal("0")
            kr_value = Decimal("0")
            us_value_krw = Decimal("0")
            
            has_holdings = any(qty > 0 for qty in holdings.values())
            
            if has_holdings:
                for stock_id, qty in holdings.items():
                    if qty <= 0:
                        continue
                    
                    stock = stocks.get(stock_id)
                    if not stock:
                        continue
                    
                    price = await get_stock_price_on_date(
                        session, stock_id, current_date, price_cache
                    )
                    
                    if price <= 0:
                        continue
                    
                    value = qty * Decimal(str(price))
                    
                    if stock.market_type == MarketType.KR:
                        kr_value += value
                        total_value_krw += value
                    else:
                        exchange_rate = Decimal("1300")
                        value_krw = value * exchange_rate
                        us_value_krw += value_krw
                        total_value_krw += value_krw
            
            if total_value_krw > 0 or total_invested > 0:
                cumulative_return = total_value_krw + total_dividends_accumulated - total_invested
                cumulative_return_pct = (
                    (cumulative_return / total_invested * 100) 
                    if total_invested > 0 else Decimal("0")
                )
                
                perf = DailyPerformance(
                    user_id=user_id,
                    record_date=current_date,
                    total_value_krw=float(total_value_krw),
                    total_invested_krw=float(total_invested),
                    kr_value=float(kr_value),
                    us_value_usd=0,
                    us_value_krw=float(us_value_krw),
                    exchange_rate=1300.0,
                    daily_pnl=0,
                    daily_pnl_percent=0,
                    cumulative_return=float(cumulative_return),
                    cumulative_return_percent=float(cumulative_return_pct),
                    total_dividends=float(total_dividends_accumulated)
                )
                session.add(perf)
                saved_count += 1
                
                if saved_count % 50 == 0:
                    await session.commit()
                    logger.info(f"  진행: {current_date} ({saved_count}일치 저장)")
            
            current_date += timedelta(days=1)
        
        await session.commit()
        
        logger.info("="*60)
        logger.info("일일 손익 계산 시작")
        logger.info("="*60)
        
        stmt = select(DailyPerformance).where(
            DailyPerformance.user_id == user_id
        ).order_by(DailyPerformance.record_date)
        result = await session.execute(stmt)
        performances = result.scalars().all()
        
        prev_value = None
        updated_count = 0
        
        for perf in performances:
            if prev_value is not None:
                daily_pnl = Decimal(str(perf.total_value_krw)) - Decimal(str(prev_value))
                daily_pnl_pct = (
                    (daily_pnl / Decimal(str(prev_value)) * 100)
                    if prev_value > 0 else Decimal("0")
                )
                
                perf.daily_pnl = float(daily_pnl)
                perf.daily_pnl_percent = float(daily_pnl_pct)
                updated_count += 1
            
            prev_value = perf.total_value_krw
        
        await session.commit()
        
        logger.info("="*60)
        logger.info(f"총 {saved_count}일치 성과 데이터 생성")
        logger.info(f"총 {updated_count}일치 일일 손익 계산 완료")
        logger.info("="*60)


async def main():
    logger.info("="*60)
    logger.info("일일 포트폴리오 성과 재계산")
    logger.info("="*60)
    
    async with async_session_maker() as session:
        stmt = select(User)
        result = await session.execute(stmt)
        users = result.scalars().all()
        
        logger.info(f"\n총 {len(users)}명의 사용자 발견")
        
        for user in users:
            logger.info(f"\n사용자: {user.email}")
            await calculate_daily_performance_for_user(user.id)
    
    logger.info("\n" + "="*60)
    logger.info("모든 사용자 성과 계산 완료!")
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())
