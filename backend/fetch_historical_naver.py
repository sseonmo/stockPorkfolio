"""
네이버 금융에서 과거 시세 데이터 수집
- KIS API 500 에러 우회용
- 종목별 첫 매수일부터 현재까지 일별 시세 수집
"""
import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Any

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select

from app.core.database import async_session_maker
from app.models.stock import Stock
from app.models.transaction import Transaction, TransactionType
from app.models.market_data import MarketDataHistory

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def fetch_naver_daily_data(
    ticker: str,
    start_date: date,
    end_date: date,
    delay: int = 1
) -> list[dict[str, Any]]:
    """
    네이버 금융 일별 시세 조회
    
    URL: https://finance.naver.com/item/sise_day.naver?code={ticker}&page={page}
    """
    await asyncio.sleep(delay)
    
    all_data = []
    page = 1
    max_pages = 100
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        
        while page <= max_pages:
            try:
                url = f"https://finance.naver.com/item/sise_day.naver?code={ticker}&page={page}"
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                table = soup.select_one('table.type2')
                
                if not table:
                    break
                
                rows = table.select('tr')
                page_has_data = False
                
                for row in rows:
                    cols = row.select('td')
                    if len(cols) < 7:
                        continue
                    
                    date_text = cols[0].get_text(strip=True)
                    if not date_text or '.' not in date_text:
                        continue
                    
                    try:
                        record_date = datetime.strptime(date_text, '%Y.%m.%d').date()
                        
                        if record_date < start_date:
                            return all_data
                        
                        if record_date > end_date:
                            continue
                        
                        page_has_data = True
                        
                        close = cols[1].get_text(strip=True).replace(',', '')
                        open_p = cols[3].get_text(strip=True).replace(',', '')
                        high = cols[4].get_text(strip=True).replace(',', '')
                        low = cols[5].get_text(strip=True).replace(',', '')
                        volume = cols[6].get_text(strip=True).replace(',', '')
                        
                        all_data.append({
                            'record_date': record_date,
                            'open_price': float(open_p) if open_p else 0,
                            'high_price': float(high) if high else 0,
                            'low_price': float(low) if low else 0,
                            'close_price': float(close) if close else 0,
                            'volume': int(volume) if volume else 0
                        })
                        
                    except (ValueError, IndexError) as e:
                        continue
                
                if not page_has_data:
                    break
                
                page += 1
                await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(f"  페이지 {page} 크롤링 실패: {e}")
                break
    
    return all_data


async def fetch_stock_historical_data(
    stock_id: int,
    ticker: str,
    name: str,
    first_buy_date: date,
    delay: int = 1
):
    async with async_session_maker() as session:
        logger.info(f"\n{'='*60}")
        logger.info(f"종목: {name} ({ticker})")
        logger.info(f"첫 매수일: {first_buy_date}")
        
        existing_stmt = select(MarketDataHistory).where(
            MarketDataHistory.stock_id == stock_id
        )
        existing_result = await session.execute(existing_stmt)
        existing_dates = {row.record_date for row in existing_result.scalars().all()}
        
        if existing_dates:
            logger.info(f"기존 데이터: {len(existing_dates)}일치")
        
        end_date = date.today()
        
        logger.info(f"수집 기간: {first_buy_date} ~ {end_date}")
        logger.info(f"네이버 금융 크롤링 시작...")
        
        data = await fetch_naver_daily_data(
            ticker=ticker,
            start_date=first_buy_date,
            end_date=end_date,
            delay=delay
        )
        
        logger.info(f"수신 데이터: {len(data)}일치")
        
        saved_count = 0
        skipped_count = 0
        
        for item in data:
            if item['record_date'] in existing_dates:
                skipped_count += 1
                continue
            
            market_data = MarketDataHistory(
                stock_id=stock_id,
                record_date=item['record_date'],
                open_price=item['open_price'],
                high_price=item['high_price'],
                low_price=item['low_price'],
                close_price=item['close_price'],
                volume=item['volume']
            )
            session.add(market_data)
            saved_count += 1
        
        await session.commit()
        
        logger.info(f"저장 완료: {saved_count}개 신규 저장, {skipped_count}개 스킵")


async def main():
    logger.info("="*60)
    logger.info("네이버 금융 과거 시세 데이터 수집")
    logger.info("="*60)
    
    async with async_session_maker() as session:
        stmt = select(Transaction).where(
            Transaction.transaction_type == TransactionType.BUY
        ).order_by(Transaction.transaction_date)
        
        result = await session.execute(stmt)
        transactions = result.scalars().all()
        
        stock_first_buy = {}
        for tx in transactions:
            if tx.stock_id not in stock_first_buy:
                stock_first_buy[tx.stock_id] = tx.transaction_date
        
        stock_stmt = select(Stock).where(Stock.id.in_(stock_first_buy.keys()))
        stock_result = await session.execute(stock_stmt)
        stocks_list = stock_result.scalars().all()
        
        stocks = [
            type('StockInfo', (), {
                'id': s.id,
                'ticker': s.ticker,
                'name': s.name,
                'first_buy_date': stock_first_buy[s.id]
            })()
            for s in stocks_list
        ]
        stocks.sort(key=lambda x: x.first_buy_date)
        
        logger.info(f"\n총 {len(stocks)}개 종목 발견")
        logger.info(f"페이지 간격: 1초")
        logger.info("")
        
        for idx, stock in enumerate(stocks, 1):
            logger.info(f"\n진행: [{idx}/{len(stocks)}]")
            
            await fetch_stock_historical_data(
                stock_id=stock.id,
                ticker=stock.ticker,
                name=stock.name,
                first_buy_date=stock.first_buy_date,
                delay=1
            )
    
    logger.info("\n" + "="*60)
    logger.info("모든 데이터 수집 완료!")
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())
