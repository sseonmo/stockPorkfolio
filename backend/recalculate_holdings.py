import asyncio
from sqlalchemy import select

from app.core.database import async_session_maker
from app.models.transaction import Transaction
from app.models.stock import Stock
from app.services.holding_service import holding_service


async def recalculate_all_holdings(user_id: int):
    async with async_session_maker() as session:
        try:
            result = await session.execute(
                select(Transaction.stock_id)
                .where(Transaction.user_id == user_id)
                .distinct()
            )
            stock_ids = [row[0] for row in result.all()]
            
            print(f"사용자 ID {user_id}의 {len(stock_ids)}개 종목에 대한 보유내역 재계산 중...")
            print("-" * 60)
            
            for stock_id in stock_ids:
                stock_result = await session.execute(
                    select(Stock).where(Stock.id == stock_id)
                )
                stock = stock_result.scalar_one_or_none()
                
                holding = await holding_service.recalculate_holding(session, user_id, stock_id)
                
                if holding:
                    print(f"✓ {stock.name}({stock.ticker}): {holding.quantity}주, 평균단가: {holding.average_cost:,.0f}원")
                else:
                    print(f"✓ {stock.name}({stock.ticker}): 보유 없음 (모두 매도됨)")
            
            await session.commit()
            
            print("-" * 60)
            print("✅ 보유내역 재계산 완료!")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ 오류 발생: {e}")
            raise


if __name__ == "__main__":
    print("=" * 60)
    print("보유내역 재계산")
    print("=" * 60)
    asyncio.run(recalculate_all_holdings(user_id=1))
