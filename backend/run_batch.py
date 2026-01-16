import asyncio
from app.tasks.batch_tasks import _update_kr_prices, _update_us_prices, _create_daily_snapshot

async def run_batch():
    print("1. Updating KR stock prices...")
    try:
        await _update_kr_prices()
        print("   SUCCESS.")
    except Exception as e:
        print(f"   FAILED: {e}")

    print("\n2. Updating US stock prices...")
    try:
        await _update_us_prices()
        print("   SUCCESS.")
    except Exception as e:
        print(f"   FAILED: {e}")

    print("\n3. Creating Daily Performance Snapshot...")
    try:
        await _create_daily_snapshot()
        print("   SUCCESS.")
    except Exception as e:
        print(f"   FAILED: {e}")

    print("\nBatch job simulation completed.")

if __name__ == "__main__":
    asyncio.run(run_batch())
