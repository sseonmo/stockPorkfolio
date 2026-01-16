import asyncio
from sqlalchemy import select
from app.core.database import async_session_maker
from app.models.user import User
from app.models.stock import Stock
from app.models.transaction import Transaction
from app.models.holding import Holding

async def main():
    async with async_session_maker() as session:
        print("--- USERS ---")
        result = await session.execute(select(User))
        users = result.scalars().all()
        for u in users:
            print(f"ID: {u.id}, Email: {u.email}")
            
        print("\n--- STOCKS ---")
        result = await session.execute(select(Stock))
        stocks = result.scalars().all()
        for s in stocks:
            print(f"ID: {s.id}, Ticker: {s.ticker}, Name: {s.name}")

        print("\n--- TRANSACTIONS ---")
        result = await session.execute(select(Transaction))
        txns = result.scalars().all()
        for t in txns:
            print(f"ID: {t.id}, User: {t.user_id}, Stock: {t.stock_id}, Type: {t.transaction_type}, Qty: {t.quantity}")

        print("\n--- HOLDINGS ---")
        result = await session.execute(select(Holding))
        holdings = result.scalars().all()
        for h in holdings:
            print(f"ID: {h.id}, User: {h.user_id}, Stock: {h.stock_id}, Qty: {h.quantity}, Total Invested: {h.total_invested}")

if __name__ == "__main__":
    asyncio.run(main())
