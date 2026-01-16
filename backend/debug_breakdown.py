import asyncio
from decimal import Decimal
from app.core.database import async_session_maker
from app.services.holding_service import holding_service
from app.models.stock import MarketType

async def main():
    async with async_session_maker() as session:
        user_id = 1
        exchange_rate = 1300.0

        print(f"--- Debugging Market Breakdown for User {user_id} ---")
        holdings = await holding_service.get_holdings_with_metrics(
            session, user_id, exchange_rate
        )

        kr_value = Decimal("0")
        kr_invested = Decimal("0")
        us_value_usd = Decimal("0")
        us_value_krw = Decimal("0")
        us_invested = Decimal("0")
        total_value_krw = Decimal("0")

        for h in holdings:
            stock = h["stock"]
            if not stock:
                continue
            
            value_krw = Decimal(str(h["current_value_krw"]))
            total_value_krw += value_krw
            
            print(f"Stock: {stock.name}, Market: {stock.market_type}, Value(KRW): {value_krw}")

            if stock.market_type == MarketType.KR:
                kr_value += value_krw
                kr_invested += Decimal(str(h["total_invested"]))
            else:
                us_value_krw += value_krw
                us_value_usd += Decimal(str(h["current_value"]))
                us_invested += Decimal(str(h["total_invested"]))

        print("\n--- Results ---")
        print(f"Total Value (KRW): {total_value_krw}")
        print(f"KR Value: {kr_value}")
        print(f"US Value (KRW): {us_value_krw}")

        result = []
        if kr_value > 0:
            result.append({"market": "KR", "value": float(kr_value)})
        if us_value_krw > 0:
            result.append({"market": "US", "value": float(us_value_krw)})
            
        print(f"Breakdown Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
