import asyncio
import csv
from datetime import datetime
from io import StringIO

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.models.stock import Stock, MarketType
from app.models.transaction import Transaction, TransactionType
from app.models.user import User


csv_data = """ticker,거래유형,수량,단가,거래일
214450,매수,5,434500,2026-01-19
012330,매수,10,391000,2026-01-14
131970,매도,19,49351,2026-01-14
131970,매도,35,50399,2026-01-13
066570,매도,27,89221,2026-01-13
214450,매수,5,467000,2026-01-12
066570,매도,30,91417,2026-01-12
035420,매수,10,251000,2026-01-09
010140,매수,50,24350,2026-01-08
010140,매수,50,24150,2026-01-05
000660,매도,10,647702,2026-01-05
010950,매도,61,82335,2026-01-05
035420,매수,1,207031,2025-01-10
005930,매수,10,57208,2025-01-10
000660,매수,1,195029,2025-01-10
000660,매수,2,190228,2025-02-05
035420,매수,1,217532,2025-02-06
005930,매수,9,52607,2025-02-06
035420,매수,2,219532,2025-03-04
005930,매수,3,56308,2025-03-04
000660,매수,2,199129,2025-03-04
035420,매수,2,200028,2025-04-08
000660,매수,2,188526,2025-04-08
005930,매수,3,57808,2025-04-08
005930,매수,10,54907,2025-05-12
000660,매수,1,192726,2025-05-12
035420,매수,1,189128,2025-05-12
005930,매수,35,60308,2025-06-11
035420,매수,8,197729,2025-06-11
000660,매수,6,229534,2025-06-11
208140,매수,100,2720,2025-06-16
000270,매수,8,98413,2025-06-16
000660,매도,26,251087,2025-06-24
035420,매도,24,246592,2025-06-24
208140,매수,100,2770,2025-07-08
005930,매수,50,63308,2025-07-08
000270,매수,10,99613,2025-07-08
005930,매수,43,70009,2025-08-05
005385,매수,12,165624,2025-08-19
005930,매수,15,67609,2025-09-03
300720,매수,80,18982,2025-09-05
005930,매수,15,69409,2025-09-05
005380,매수,11,222031,2025-09-05
086790,매수,30,81711,2025-09-08
005380,매수,7,216532,2025-09-17
030200,매수,10,50007,2025-09-24
005930,매도,130,89152,2025-10-13
005380,매수,23,216530,2025-10-14
300720,매수,82,18182,2025-10-15
086790,매수,30,84912,2025-10-15
005930,매도,60,108122,2025-11-06
005930,매수,25,98113,2025-11-07
005380,매수,10,260539,2025-11-07
010950,매수,33,77011,2025-11-10
005930,매수,50,99914,2025-11-10
066570,매수,28,89013,2025-11-11
034020,매수,32,80112,2025-11-18
086790,매수,25,93013,2025-11-19
005380,매수,10,272038,2025-11-19
086790,매수,27,92212,2025-11-20
066570,매수,29,86912,2025-11-21
034020,매수,34,74410,2025-11-21
010950,매수,28,89812,2025-11-21
005380,매수,10,264537,2025-11-21
039490,매수,10,262036,2025-11-25
035420,매수,10,246534,2025-12-05
030200,매도,10,52713,2025-12-09
005380,매도,36,314483,2025-12-10
000270,매도,18,125007,2025-12-10
010140,매수,100,27053,2025-12-11
300720,매도,162,20138,2025-12-16
000660,매수,20,547000,2025-12-17
208140,매도,200,2755,2025-12-17
131970,매수,55,46150,2025-12-26
006800,매수,220,23750,2025-12-26"""


STOCK_INFO = {
    "214450": {"name": "파마리서치", "exchange": "KOSDAQ", "sector": "제약"},
    "012330": {"name": "현대모비스", "exchange": "KOSPI", "sector": "자동차"},
    "131970": {"name": "테스나", "exchange": "KOSDAQ", "sector": "IT"},
    "066570": {"name": "LG전자", "exchange": "KOSPI", "sector": "전기전자"},
    "035420": {"name": "NAVER", "exchange": "KOSPI", "sector": "IT"},
    "010140": {"name": "삼성중공업", "exchange": "KOSPI", "sector": "조선"},
    "000660": {"name": "SK하이닉스", "exchange": "KOSPI", "sector": "반도체"},
    "010950": {"name": "S-Oil", "exchange": "KOSPI", "sector": "정유화학"},
    "005930": {"name": "삼성전자", "exchange": "KOSPI", "sector": "전기전자"},
    "208140": {"name": "정상제이엘에스", "exchange": "KOSDAQ", "sector": "운송"},
    "000270": {"name": "기아", "exchange": "KOSPI", "sector": "자동차"},
    "005385": {"name": "현대차우", "exchange": "KOSPI", "sector": "자동차"},
    "300720": {"name": "한일시멘트", "exchange": "KOSPI", "sector": "건설"},
    "005380": {"name": "현대차", "exchange": "KOSPI", "sector": "자동차"},
    "086790": {"name": "하나금융지주", "exchange": "KOSPI", "sector": "금융"},
    "030200": {"name": "KT", "exchange": "KOSPI", "sector": "통신"},
    "034020": {"name": "두산에너빌리티", "exchange": "KOSPI", "sector": "기계"},
    "039490": {"name": "키움증권", "exchange": "KOSPI", "sector": "증권"},
    "006800": {"name": "미래에셋증권", "exchange": "KOSPI", "sector": "증권"},
}


async def get_or_create_stock(session: AsyncSession, ticker: str) -> Stock:
    result = await session.execute(select(Stock).where(Stock.ticker == ticker))
    stock = result.scalar_one_or_none()
    
    if not stock:
        info = STOCK_INFO.get(ticker, {"name": ticker, "exchange": "KOSPI", "sector": None})
        stock = Stock(
            ticker=ticker,
            name=info["name"],
            market_type=MarketType.KR,
            exchange=info["exchange"],
            sector=info["sector"],
            currency="KRW",
        )
        session.add(stock)
        await session.flush()
        print(f"✓ 종목 생성: {ticker} - {info['name']}")
    
    return stock


async def get_user_by_email(session: AsyncSession, email: str) -> User:
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise Exception(f"User not found: {email}")
    
    return user


async def import_transactions():
    async with async_session_maker() as session:
        try:
            user = await get_user_by_email(session, "mo3509@gmail.com")
            print(f"\n사용자: {user.name} (ID: {user.id})")
            print("-" * 60)
            
            csv_file = StringIO(csv_data)
            reader = csv.DictReader(csv_file)
            
            transactions_created = 0
            
            for row in reader:
                ticker = row["ticker"]
                transaction_type_kr = row["거래유형"]
                quantity = float(row["수량"])
                price = float(row["단가"])
                transaction_date = datetime.strptime(row["거래일"], "%Y-%m-%d").date()
                
                transaction_type = TransactionType.BUY if transaction_type_kr == "매수" else TransactionType.SELL
                stock = await get_or_create_stock(session, ticker)
                
                transaction = Transaction(
                    user_id=user.id,
                    stock_id=stock.id,
                    transaction_type=transaction_type,
                    quantity=quantity,
                    price=price,
                    exchange_rate=1.0,
                    fees=0.0,
                    transaction_date=transaction_date,
                    notes=None,
                )
                session.add(transaction)
                transactions_created += 1
                
                total_amount = quantity * price
                print(f"✓ {transaction_date} | {stock.name}({ticker}) | {transaction_type_kr} {quantity}주 @ {price:,.0f}원 = {total_amount:,.0f}원")
            
            await session.commit()
            
            print("-" * 60)
            print(f"\n✅ 총 {transactions_created}건의 거래내역이 저장되었습니다.")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ 오류 발생: {e}")
            raise


if __name__ == "__main__":
    print("=" * 60)
    print("거래내역 일괄 입력 시작")
    print("=" * 60)
    asyncio.run(import_transactions())
