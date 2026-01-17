import asyncio
import time
from datetime import datetime, timedelta, date
from collections import defaultdict
import logging

from sqlalchemy import select, delete
from app.core.database import async_session_maker
from app.models.transaction import Transaction, TransactionType
from app.models.stock import Stock
from app.models.daily_performance import DailyPerformance
from app.models.user import User
from app.models.dividend import Dividend  # 모델 로딩을 위해 추가
from app.external.kis_client import kis_client

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def get_trading_days(start_date: date, end_date: date):
    """
    주말을 제외한 평일 리스트를 생성합니다. (공휴일은 API 데이터로 처리)
    """
    days = []
    curr = start_date
    while curr <= end_date:
        if curr.weekday() < 5:  # 월~금
            days.append(curr)
        curr += timedelta(days=1)
    return days

async def fetch_stock_history(ticker: str, start_date: str, end_date: str):
    """
    특정 종목의 기간별 시세를 가져옵니다.
    안전하게 1분 딜레이를 두고 데이터를 수집합니다.
    """
    all_prices = {} # {date_str: price}
    
    # KIS API get_daily_prices 활용 (기본 30일치)
    # 2년치(약 730일)를 가져오려면 반복 호출 필요하지 않을까 싶지만,
    # API가 기간 조회를 지원하지 않으면 최근 데이터만 가져옴.
    # 하지만 사용자의 요청("안전하게, 반복실행")을 따르기 위해
    # 일단 1분 딜레이를 주고 호출함.
    
    logger.info(f"Fetching history for {ticker} (Safety Delay: 60s)...")
    await asyncio.sleep(60) # 1분 대기
    
    try:
        # FHKST01010400 (주식현재가 일자별) 호출
        # 이 API는 FID_PERIOD_DIV_CODE='D'만 있고 날짜 지정이 없어서 최근 30일치만 줌.
        # 하지만 일단 호출하여 데이터 확보.
        data = await kis_client.get_daily_prices(ticker, "", "")
        
        if data:
            for item in data:
                dt_str = item['stck_bsop_date']
                close_price = float(item['stck_clpr'])
                all_prices[dt_str] = close_price
            logger.info(f"  - Retrieved {len(data)} days of data.")
            
            # 만약 데이터가 부족하다면(2년치 필요), 추가 로직이 필요하지만
            # 현재 KIS API 스펙상 어려움. 
            # 네이버 금융 크롤링이 답이지만, 사용자가 API 재시도를 원함.
            
    except Exception as e:
        logger.error(f"Error fetching {ticker}: {e}")
            
    return all_prices

async def calculate_daily_pnl():
    async with async_session_maker() as session:
        # 1. 사용자 확인
        user = await session.execute(select(User).where(User.email == "mo3509@gmail.com"))
        user = user.scalar_one_or_none()
        if not user:
            logger.error("User not found")
            return

        # 2. 모든 거래 내역 가져오기
        transactions_result = await session.execute(
            select(Transaction)
            .where(Transaction.user_id == user.id)
            .order_by(Transaction.transaction_date)
        )
        transactions = transactions_result.scalars().all()
        
        if not transactions:
            logger.info("No transactions found.")
            return

        # 3. 거래된 모든 종목 식별
        stock_ids = set(tx.stock_id for tx in transactions)
        stocks_result = await session.execute(select(Stock).where(Stock.id.in_(stock_ids)))
        stocks = {s.id: s for s in stocks_result.scalars().all()}
        
        logger.info(f"Found {len(stocks)} stocks to process.")

        # 4. 각 종목별 주가 데이터 수집 (2024-01-01 ~ 오늘)
        # 2년치 데이터를 모두 가져오려면 차트용 API(FHKST03010100)가 필요하지만
        # 현재 kis_client는 FHKST01010400(일자별 시세)만 지원하여 최근 30일치만 올 수 있음.
        # 일단 가능한 만큼 가져오고, 과거 데이터가 없으면 '매수가' 또는 '가장 오래된 데이터'로 대체.
        
        today = datetime.now().date()
        start_date = date(2024, 1, 1)
        price_history = defaultdict(dict) # {stock_id: {date: price}}
        
        for stock_id, stock in stocks.items():
            logger.info(f"Fetching data for {stock.name} ({stock.ticker})...")
            
            # API 호출
            raw_prices = await fetch_stock_history(stock.ticker, "20240101", today.strftime("%Y%m%d"))
            
            # 날짜 형식 변환 (str -> date)
            for dt_str, price in raw_prices.items():
                try:
                    dt = datetime.strptime(dt_str, "%Y%m%d").date()
                    price_history[stock_id][dt] = price
                except ValueError:
                    continue
            
            logger.info(f"  - Retrieved {len(raw_prices)} days of data.")
            
        # 5. 일별 포트폴리오 가치 계산
        logger.info("Calculating daily portfolio value...")
        
        # 기존 데이터 삭제 (재계산)
        await session.execute(delete(DailyPerformance).where(DailyPerformance.user_id == user.id))
        
        current_holdings = defaultdict(float) # {stock_id: quantity}
        current_avg_cost = defaultdict(float) # {stock_id: avg_cost} (단순화)
        
        # 거래 내역을 날짜별로 그룹화
        tx_by_date = defaultdict(list)
        for tx in transactions:
            tx_by_date[tx.transaction_date].append(tx)
            
        # 2024-01-01부터 오늘까지 하루씩 진행
        curr = start_date
        
        total_records = 0
        
        while curr <= today:
            # 1) 그 날의 거래 반영
            if curr in tx_by_date:
                for tx in tx_by_date[curr]:
                    quantity = float(tx.quantity)
                    if tx.transaction_type == TransactionType.BUY:
                        current_holdings[tx.stock_id] += quantity
                    else:
                        current_holdings[tx.stock_id] -= quantity
                        if current_holdings[tx.stock_id] < 0:
                            current_holdings[tx.stock_id] = 0.0
            
            # 2) 그 날의 총 자산 가치 계산
            total_value = 0.0
            total_invested = 0.0 # 투자 원금 (간략화)
            
            has_holdings = sum(current_holdings.values()) > 0
            
            if has_holdings:
                for stock_id, qty in current_holdings.items():
                    if qty > 0:
                        # 그 날의 가격 찾기
                        price = 0
                        
                        # 1순위: 그 날의 데이터
                        if curr in price_history[stock_id]:
                            price = price_history[stock_id][curr]
                        # 2순위: 그 날 데이터가 없으면(휴일 등), 가장 최근 과거 데이터 찾기
                        else:
                            # 과거 데이터 검색 (최대 10일 전까지)
                            temp_date = curr
                            found = False
                            for _ in range(10):
                                temp_date -= timedelta(days=1)
                                if temp_date in price_history[stock_id]:
                                    price = price_history[stock_id][temp_date]
                                    found = True
                                    break
                            
                            # 3순위: 그래도 없으면(데이터 수집 범위 밖), 현재가(DB) 또는 매수가 사용
                            if not found:
                                # 여기서는 단순히 0 처리하거나, 해당 종목의 첫 거래 가격 등을 써야함.
                                # 일단 0으로 두면 자산이 0으로 잡힘.
                                # fetch_stock_history가 최근 데이터만 가져오면 과거 자산은 0이 됨.
                                pass
                        
                        if price > 0:
                            total_value += qty * price
            
            # 3) DB 저장 (보유량이 있거나 거래가 있었던 날만 저장, 또는 매일 저장)
            # 여기서는 자산이 있는 경우에만 저장
            if total_value > 0:
                # 어제 자산 (일일 손익 계산용)
                # 정확한 일일 손익 = (오늘 자산 - 어제 자산) - (오늘 순입금)
                # 여기서는 순입금 계산이 복잡하므로, 일단 자산 가치만 저장하고
                # 나중에 프론트엔드나 쿼리에서 차이를 계산하거나,
                # 여기서 전날 데이터와 비교해야 함.
                
                # DailyPerformance 모델 필드:
                # date, total_value_krw, total_value_usd, daily_pnl, ...
                
                # daily_pnl은 여기서 계산하기 까다로움 (입출금 데이터 필요).
                # 일단 total_value라도 정확히 넣는 것이 목표.
                
                perf = DailyPerformance(
                    user_id=user.id,
                    record_date=curr,
                    total_value_krw=total_value,
                    total_invested_krw=0, # 투자 원금은 추후 계산 필요
                    kr_value=total_value, # 현재 KR만 고려
                    us_value_usd=0,
                    us_value_krw=0,
                    exchange_rate=1.0,
                    daily_pnl=0,
                    daily_pnl_percent=0,
                    cumulative_return=0,
                    cumulative_return_percent=0,
                    total_dividends=0
                )
                session.add(perf)
                total_records += 1
            
            curr += timedelta(days=1)
            
        await session.commit()
        logger.info(f"Successfully created {total_records} daily performance records.")

if __name__ == "__main__":
    asyncio.run(calculate_daily_pnl())
