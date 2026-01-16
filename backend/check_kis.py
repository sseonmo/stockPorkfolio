import asyncio
from app.external.kis_client import kis_client
from app.core.config import settings

async def main():
    print(f"Checking KIS API Configuration...")
    print(f"App Key Loaded: {'Yes' if settings.kis_app_key else 'No'}")
    print(f"App Secret Loaded: {'Yes' if settings.kis_app_secret else 'No'}")
    
    if not settings.kis_app_key:
        print("KIS API key is missing. Cannot verify connection.")
        return

    print("\nAttempting to connect to KIS API (Access Token)...")
    try:
        token = await kis_client._get_access_token()
        print(f"Success! Access Token retrieved: {token[:10]}...")
    except Exception as e:
        print(f"Failed to get access token: {e}")
        return

    print("\nAttempting to search for 'Samsung Electronics'...")
    try:
        # Search for Samsung Electronics (005930)
        results = await kis_client.search_stock("005930")
        print(f"Search Results: {results}")
        if results:
            print("Successfully retrieved stock info.")
        else:
            print("Search returned empty list.")
    except Exception as e:
        print(f"Failed search: {e}")

if __name__ == "__main__":
    asyncio.run(main())
