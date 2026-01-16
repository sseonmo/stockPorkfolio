import asyncio
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import async_session_maker
from app.models.holding import Holding
from app.services.holding_service import holding_service

async def main():
    async with async_session_maker() as session:
        user_id = 1
        print(f"Checking for User ID: {user_id}")
        
        # Test holding_service directly
        # We need to mock yfinance_client.get_exchange_rate or pass it
        exchange_rate = 1300.0
        
        try:
            holdings = await holding_service.get_holdings_with_metrics(session, user_id, exchange_rate)
            print(f"Found {len(holdings)} holdings with metrics")
            
            total_value_krw = Decimal("0")
            for h in holdings:
                print(f"Stock: {h['stock'].name}, Qty: {h['quantity']}, Curr Price: {h['stock'].current_price}, Avg Cost: {h['average_cost']}")
                print(f"  -> Value KRW: {h['current_value_krw']}")
                total_value_krw += Decimal(str(h["current_value_krw"]))
                
            print(f"Total Value KRW: {total_value_krw}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
