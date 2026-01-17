"""
과거 시세 데이터 수집 스크립트
- 종목별 첫 매수일부터 현재까지 일별 시세를 수집합니다
- KIS API 국내주식 기간별시세 API 사용 (FHKST03010100)
- API rate limit 고려하여 10초 간격으로 호출합니다
"""
import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Any

from sqlalchemy import select, and_
from app.core.database import async_session_maker
from app.models.stock import Stock
from app.models.transaction import Transaction, TransactionType
from app.models.market_data import MarketDataHistory
from app.external.kis_client import kis_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def get_period_chart_data(
    ticker: str,
    start_date: str,
    end_date: str,
    delay: int = 10
) -> list[dict[str, Any]]:
    """
    KIS API 국내주식 기간별시세 조회 (FHKST03010100)
    
    Args:
        ticker: 종목코드 (6자리)
        start_date: 시작일 (YYYYMMDD)
        end_date: 종료일 (YYYYMMDD)
        delay: API 호출 간격 (초)
    
    Returns:
        [
            {
                'stck_bsop_date': '20240808',  # 영업일자
                'stck_oprc': '72000',           # 시가
                'stck_hgpr': '73000',           # 고가
                'stck_lwpr': '71500',           # 저가
                'stck_clpr': '72500',           # 종가
                'acml_vol': '12345678'          # 누적거래량
            },
            ...
        ]
    """
    logger.info(f"  API 호출 대기 중... ({delay}초)")
    await asyncio.sleep(delay)
    
    try:
        result = await kis_client._request(
            "GET",
            "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
            "FHKST03010100",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",  # 시장분류코드 (J: 주식)
                "FID_INPUT_ISCD": ticker,        # 종목코드
                "FID_INPUT_DATE_1": start_date,  # 시작일자
                "FID_INPUT_DATE_2": end_date,    # 종료일자
                "FID_PERIOD_DIV_CODE": "D",      # 기간분류코드 (D:일, W:주, M:월)
                "FID_ORG_ADJ_PRC": "0",          # 수정주가 (0:수정주가반영, 1:수정주가미반영)
            },
        )
        
        output = result.get("output2", [])  # output2에 일별 데이터 리스트
        logger.info(f"  ✓ {len(output)}개 데이터 수신")
        return output
    
    except Exception as e:
        logger.error(f"  ✗ API 호출 실패: {e}")
        return []


async def fetch_stock_historical_data(
    stock_id: int,
    ticker: str,
    name: str,
    first_buy_date: date,
    delay: int = 10
):
    """
    특정 종목의 과거 시세 데이터를 수집하여 DB에 저장
    
    - KIS API는 한 번에 최대 100개 데이터 반환
    - 100일 단위로 끊어서 여러 번 호출
    """
    async with async_session_maker() as session:
        logger.info(f"\n{'='*60}")
        logger.info(f"종목: {name} ({ticker})")
        logger.info(f"첫 매수일: {first_buy_date}")
        
        # 이미 수집된 데이터 확인
        existing_stmt = select(MarketDataHistory).where(
            MarketDataHistory.stock_id == stock_id
        )
        existing_result = await session.execute(existing_stmt)
        existing_dates = {row.record_date for row in existing_result.scalars().all()}
        
        if existing_dates:
            logger.info(f"기존 데이터: {len(existing_dates)}일치")
        
        # 수집 기간 설정
        end_date = date.today()
        current_start = first_buy_date
        
        all_data = []
        api_call_count = 0
        
        # 100일 단위로 끊어서 수집
        while current_start <= end_date:
            # 현재 구간의 종료일 계산 (최대 100일)
            current_end = min(current_start + timedelta(days=99), end_date)
            
            logger.info(f"기간: {current_start} ~ {current_end}")
            
            # API 호출
            chart_data = await get_period_chart_data(
                ticker=ticker,
                start_date=current_start.strftime("%Y%m%d"),
                end_date=current_end.strftime("%Y%m%d"),
                delay=delay
            )
            
            api_call_count += 1
            
            if chart_data:
                all_data.extend(chart_data)
            
            # 다음 구간으로 이동
            current_start = current_end + timedelta(days=1)
        
        logger.info(f"총 API 호출: {api_call_count}회")
        logger.info(f"수신 데이터: {len(all_data)}일치")
        
        # DB 저장
        saved_count = 0
        skipped_count = 0
        
        for item in all_data:
            try:
                record_date = datetime.strptime(item['stck_bsop_date'], "%Y%m%d").date()
                
                # 이미 존재하는 데이터는 스킵
                if record_date in existing_dates:
                    skipped_count += 1
                    continue
                
                market_data = MarketDataHistory(
                    stock_id=stock_id,
                    record_date=record_date,
                    open_price=float(item['stck_oprc']),
                    high_price=float(item['stck_hgpr']),
                    low_price=float(item['stck_lwpr']),
                    close_price=float(item['stck_clpr']),
                    volume=int(item['acml_vol'])
                )
                session.add(market_data)
                saved_count += 1
                
            except Exception as e:
                logger.error(f"  데이터 파싱 오류: {item}, {e}")
                continue
        
        await session.commit()
        
        logger.info(f"저장 완료: {saved_count}개 신규 저장, {skipped_count}개 스킵")


async def main():
    """
    메인 실행 함수
    - 보유 종목의 첫 매수일부터 과거 시세 데이터 수집
    """
    logger.info("="*60)
    logger.info("과거 시세 데이터 수집 시작")
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
        logger.info(f"API 호출 간격: 10초")
        
        # 예상 소요 시간 계산
        total_days = sum(
            (date.today() - stock.first_buy_date).days 
            for stock in stocks
        )
        estimated_api_calls = (total_days // 100) + len(stocks)
        estimated_minutes = (estimated_api_calls * 10) // 60
        
        logger.info(f"예상 API 호출: 약 {estimated_api_calls}회")
        logger.info(f"예상 소요 시간: 약 {estimated_minutes}분")
        logger.info("")
        
        for idx, stock in enumerate(stocks, 1):
            logger.info(f"\n진행: [{idx}/{len(stocks)}]")
            
            await fetch_stock_historical_data(
                stock_id=stock.id,
                ticker=stock.ticker,
                name=stock.name,
                first_buy_date=stock.first_buy_date,
                delay=10
            )
    
    logger.info("\n" + "="*60)
    logger.info("모든 데이터 수집 완료!")
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())
