"""
종목별 일일 손익 계산 및 저장
- 거래 내역으로 일별 보유수량 계산
- 시세 데이터로 일별 손익 계산
- stock_daily_performances 테이블에 저장
"""
import asyncio
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from collections import defaultdict

from sqlalchemy import select, delete
from app.core.database import async_session_maker
from app.models.user import User
from app.models.stock import Stock
from app.models.transaction import Transaction, TransactionType
from app.models.market_data import MarketDataHistory
from app.models.stock_daily_performance import StockDailyPerformance

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def calculate_stock_daily_pnl_for_user(user_id: int):
    async with async_session_maker() as session:
        logger.info("="*60)
        logger.info(f"사용자 ID {user_id} 종목별 일일 손익 계산 시작")
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
        
        await session.execute(
            delete(StockDailyPerformance).where(StockDailyPerformance.user_id == user_id)
        )
        await session.commit()
        logger.info("기존 데이터 삭제 완료")
        
        tx_by_date = defaultdict(list)
        for tx in transactions:
            tx_by_date[tx.transaction_date].append(tx)
        
        holdings = defaultdict(Decimal)
        
        current_date = first_date
        saved_count = 0
        prev_prices = {}
        
        while current_date <= last_date:
            if current_date in tx_by_date:
                for tx in tx_by_date[current_date]:
                    qty = Decimal(str(tx.quantity))
                    
                    if tx.transaction_type == TransactionType.BUY:
                        holdings[tx.stock_id] += qty
                    elif tx.transaction_type == TransactionType.SELL:
                        holdings[tx.stock_id] -= qty
                        if holdings[tx.stock_id] < 0:
                            holdings[tx.stock_id] = Decimal("0")
            
            for stock_id, qty in holdings.items():
                if qty <= 0:
                    continue
                
                stmt = select(MarketDataHistory).where(
                    MarketDataHistory.stock_id == stock_id,
                    MarketDataHistory.record_date == current_date
                )
                result = await session.execute(stmt)
                market_data = result.scalar_one_or_none()
                
                if not market_data:
                    for days_back in range(1, 11):
                        past_date = current_date - timedelta(days=days_back)
                        stmt = select(MarketDataHistory).where(
                            MarketDataHistory.stock_id == stock_id,
                            MarketDataHistory.record_date == past_date
                        )
                        result = await session.execute(stmt)
                        market_data = result.scalar_one_or_none()
                        if market_data:
                            break
                
                if not market_data:
                    continue
                
                close_price = Decimal(str(market_data.close_price))
                prev_close = prev_prices.get(stock_id, close_price)
                
                position_value = qty * close_price
                daily_pnl = qty * (close_price - prev_close)
                daily_pnl_pct = ((close_price - prev_close) / prev_close * 100) if prev_close > 0 else Decimal("0")
                
                stock_perf = StockDailyPerformance(
                    user_id=user_id,
                    stock_id=stock_id,
                    record_date=current_date,
                    quantity=float(qty),
                    close_price=float(close_price),
                    prev_close_price=float(prev_close),
                    daily_pnl=float(daily_pnl),
                    daily_pnl_percent=float(daily_pnl_pct),
                    position_value=float(position_value)
                )
                session.add(stock_perf)
                saved_count += 1
                
                prev_prices[stock_id] = close_price
            
            if saved_count % 100 == 0 and saved_count > 0:
                await session.commit()
                logger.info(f"  진행: {current_date} ({saved_count}건 저장)")
            
            current_date += timedelta(days=1)
        
        await session.commit()
        
        logger.info("="*60)
        logger.info(f"총 {saved_count}건 종목별 일일 손익 데이터 생성 완료")
        logger.info("="*60)


async def main():
    logger.info("="*60)
    logger.info("종목별 일일 손익 계산")
    logger.info("="*60)
    
    async with async_session_maker() as session:
        stmt = select(User)
        result = await session.execute(stmt)
        users = result.scalars().all()
        
        logger.info(f"\n총 {len(users)}명의 사용자 발견")
        
        for user in users:
            logger.info(f"\n사용자: {user.email}")
            await calculate_stock_daily_pnl_for_user(user.id)
    
    logger.info("\n" + "="*60)
    logger.info("모든 사용자 종목별 손익 계산 완료!")
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())
