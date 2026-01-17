"""
섹터 정보가 없는 종목들의 섹터 정보를 yfinance를 통해 업데이트합니다.
한국 주식의 경우 .KS (코스피) 또는 .KQ (코스닥) 접미사를 붙여 조회합니다.
"""
import asyncio
import logging
from sqlalchemy import select, or_
import yfinance as yf

from app.core.database import async_session_maker
from app.models.stock import Stock, MarketType

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def update_missing_sectors():
    async with async_session_maker() as session:
        # 섹터 정보가 없는 종목 조회
        stmt = select(Stock).where(
            or_(
                Stock.sector.is_(None),
                Stock.sector == '',
                Stock.sector == 'Unknown'
            )
        )
        result = await session.execute(stmt)
        stocks = result.scalars().all()
        
        logger.info(f"섹터 정보 누락 종목: {len(stocks)}개")
        
        updated_count = 0
        
        for stock in stocks:
            logger.info(f"처리 중: {stock.name} ({stock.ticker})")
            
            sector = None
            
            if stock.market_type == MarketType.KR:
                # 한국 주식: .KS 또는 .KQ 시도
                suffixes = ['.KS', '.KQ']
                for suffix in suffixes:
                    try:
                        yf_ticker = f"{stock.ticker}{suffix}"
                        info = yf.Ticker(yf_ticker).info
                        if info and 'sector' in info:
                            sector = info['sector']
                            logger.info(f"  -> 찾음 ({yf_ticker}): {sector}")
                            break
                    except Exception as e:
                        logger.error(f"  -> 에러 ({stock.ticker}{suffix}): {e}")
            else:
                # 미국 주식
                try:
                    info = yf.Ticker(stock.ticker).info
                    if info and 'sector' in info:
                        sector = info['sector']
                        logger.info(f"  -> 찾음 ({stock.ticker}): {sector}")
                except Exception as e:
                    logger.error(f"  -> 에러 ({stock.ticker}): {e}")
            
            if sector:
                stock.sector = sector
                updated_count += 1
            else:
                logger.warning(f"  -> 섹터 정보 찾지 못함")
                # 계속 검색되지 않도록 'Unknown' 대신 '기타' 또는 다른 값으로 설정할지 고려
                # 여기서는 일단 둠
        
        if updated_count > 0:
            await session.commit()
            logger.info(f"총 {updated_count}개 종목 섹터 정보 업데이트 완료")
        else:
            logger.info("업데이트된 종목 없음")

if __name__ == "__main__":
    asyncio.run(update_missing_sectors())
