import asyncio
from app.core.database import get_db_context
from app.models.batch_job import BatchJobStatus
from sqlalchemy import select, desc

async def check_batch_status():
    async with get_db_context() as db:
        print("Checking recent batch jobs from DB...")
        stmt = (
            select(BatchJobStatus)
            .order_by(desc(BatchJobStatus.started_at))
            .limit(10)
        )
        result = await db.execute(stmt)
        jobs = result.scalars().all()
        
        if not jobs:
            print("No batch job records found.")
        else:
            print(f"{'Job Name':<35} | {'Status':<10} | {'Created At':<25} | {'Msg'}")
            print("-" * 100)
            for job in jobs:
                print(f"{job.job_name:<35} | {job.status:<10} | {str(job.started_at):<25} | {job.error_message or ''}")

if __name__ == "__main__":
    asyncio.run(check_batch_status())
