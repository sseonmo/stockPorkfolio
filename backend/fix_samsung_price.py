import asyncio
from app.core.database import async_session_maker
from app.models.stock import Stock
from sqlalchemy import select

async def update_samsung_price():
    async with async_session_maker() as session:
        result = await session.execute(
            select(Stock).where(Stock.ticker == '005930')
        )
        stock = result.scalar_one_or_none()
        
        if stock:
            print(f"변경 전 가격: {stock.current_price}원")
            stock.current_price = 149500.0
            await session.commit()
            print(f"변경 후 가격: {stock.current_price}원")
            print("✅ 삼성전자 가격이 149,500원으로 수정되었습니다.")
        else:
            print('삼성전자 종목을 찾을 수 없습니다.')

if __name__ == "__main__":
    asyncio.run(update_samsung_price())
