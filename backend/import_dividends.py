import asyncio
import csv
from datetime import datetime
from io import StringIO

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.models.stock import Stock
from app.models.dividend import Dividend
from app.models.user import User

csv_data = """ticker,종목명,거래유형,배당금,입금일
005380,현대차,배당금입금,175550,2025-12-31
086790,하나금융지주,배당금입금,46710,2025-11-28
030200,KT,배당금입금,6000,2025-11-20
005930,삼성전자,배당금입금,80140,2025-11-19
005380,현대차,배당금입금,25380,2025-09-30
005930,삼성전자,배당금입금,41301,2025-08-20
000660,SK하이닉스,배당금입금,6350,2025-06-27
005930,삼성전자,배당금입금,26255,2025-05-20
000660,SK하이닉스,배당금입금,16560,2025-04-25
005930,삼성전자,배당금입금,19349,2025-04-18
035420,NAVER,배당금입금,10520,2025-04-16
005930,삼성전자,배당금입금,5776,2024-11-20
000660,SK하이닉스,배당금입금,1200,2024-11-18"""

async def get_user_by_email(session: AsyncSession, email: str) -> User:
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise Exception(f"User not found: {email}")
    return user

async def get_stock_by_ticker(session: AsyncSession, ticker: str) -> Stock:
    result = await session.execute(select(Stock).where(Stock.ticker == ticker))
    stock = result.scalar_one_or_none()
    if not stock:
        # Stock이 없으면 에러 (거래 내역이 먼저 있어야 함)
        # 하지만 혹시 모르니 생성 로직 대신 에러 처리
        raise Exception(f"Stock not found: {ticker}")
    return stock

async def import_dividends():
    async with async_session_maker() as session:
        try:
            user = await get_user_by_email(session, "mo3509@gmail.com")
            print(f"User: {user.name} ({user.email})")
            
            csv_file = StringIO(csv_data)
            reader = csv.DictReader(csv_file)
            
            count = 0
            for row in reader:
                ticker = row["ticker"]
                amount = float(row["배당금"])
                date_str = row["입금일"]
                dividend_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                
                stock = await get_stock_by_ticker(session, ticker)
                
                # 중복 확인 (같은 날짜, 같은 종목, 같은 금액이면 스킵)
                stmt = select(Dividend).where(
                    Dividend.user_id == user.id,
                    Dividend.stock_id == stock.id,
                    Dividend.dividend_date == dividend_date,
                    Dividend.amount == amount
                )
                existing = await session.execute(stmt)
                if existing.scalar_one_or_none():
                    print(f"Skipping duplicate: {date_str} {stock.name} {amount}")
                    continue
                
                # 배당금 저장 (Tax는 0으로 가정, Amount는 세전/세후 구분 없이 입력값 사용)
                # 만약 입력값이 세후라면 tax를 역산해야 하지만, 정보가 없으므로 0 처리.
                dividend = Dividend(
                    user_id=user.id,
                    stock_id=stock.id,
                    amount=amount,
                    tax=0,
                    currency="KRW",
                    dividend_date=dividend_date,
                    notes="CSV Import"
                )
                session.add(dividend)
                count += 1
                print(f"Importing: {date_str} {stock.name} {amount:,.0f}원")
                
            await session.commit()
            print(f"\n✅ Successfully imported {count} dividends.")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(import_dividends())
