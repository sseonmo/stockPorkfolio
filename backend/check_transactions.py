import asyncio
from sqlalchemy import select, func
from app.core.database import async_session_maker
from app.models.transaction import Transaction

async def check_transactions():
    async with async_session_maker() as session:
        result = await session.execute(
            select(
                func.extract('year', Transaction.transaction_date).label('year'),
                func.count(Transaction.id).label('count')
            )
            .where(Transaction.user_id == 1)
            .group_by('year')
            .order_by('year')
        )
        
        year_counts = result.all()
        
        print("=" * 60)
        print("사용자 ID 1의 연도별 거래 건수")
        print("=" * 60)
        total = 0
        for year, count in year_counts:
            print(f"{year}년: {count}건")
            total += count
        print("-" * 60)
        print(f"총 {total}건")

if __name__ == "__main__":
    asyncio.run(check_transactions())
