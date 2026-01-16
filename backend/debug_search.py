import asyncio
from app.external.kis_client import kis_client
from app.core.config import settings

async def main():
    if not settings.kis_app_key:
        print("KIS API key is missing.")
        return

    print("Searching for '두산테스나'...")
    try:
        # Search by name
        results = await kis_client.search_stock("두산테스나")
        print(f"Results: {results}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
