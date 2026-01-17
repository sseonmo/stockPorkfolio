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
035420,매수,2,209531,2024-12-05
005930,매수,21,53709,2024-12-05
000660,매수,3,161724,2024-12-05
035420,매수,2,169625,2024-11-05
000660,매수,5,181927,2024-11-05
005930,매수,9,56008,2024-10-29
005930,매수,17,61008,2024-10-08
005930,매수,16,66509,2024-09-12
035420,매수,2,154520,2024-09-11
000660,매수,4,152022,2024-09-11
035420,매수,3,158223,2024-08-08"""


STOCK_INFO = {
    "035420": {"name": "NAVER", "exchange": "KOSPI", "sector": "IT"},
    "005930": {"name": "삼성전자", "exchange": "KOSPI", "sector": "전기전자"},
    "000660": {"name": "SK하이닉스", "exchange": "KOSPI", "sector": "반도체"},
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


async def get_default_user(session: AsyncSession) -> User:
    result = await session.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    
    if not user:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        user = User(
            email="admin@example.com",
            name="관리자",
            hashed_password=pwd_context.hash("admin123"),
        )
        session.add(user)
        await session.flush()
        print(f"✓ 기본 사용자 생성: {user.email}")
    
    return user


async def import_transactions():
    async with async_session_maker() as session:
        try:
            user = await get_default_user(session)
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
