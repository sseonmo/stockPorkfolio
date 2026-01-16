import asyncio
from app.external.kis_client import kis_client
from app.core.config import settings

async def main():
    if not settings.kis_app_key:
        print("KIS API key is missing.")
        return

    # Check Doosan Tesna (131970)
    ticker = "131970" 
    print(f"Fetching price for {ticker}...")
    try:
        price = await kis_client.get_stock_price(ticker)
        print(f"Price Info: {price}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
