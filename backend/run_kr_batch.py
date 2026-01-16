import asyncio
from app.tasks.batch_tasks import _update_kr_prices

async def main():
    print("Updating KR stock prices...")
    try:
        await _update_kr_prices()
        print("SUCCESS: KR stock prices updated.")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(main())
