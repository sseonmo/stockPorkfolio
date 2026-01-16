from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "stockflow",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.batch_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Seoul",
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3000,
    result_expires=3600,
    broker_connection_retry_on_startup=True,
)

celery_app.conf.beat_schedule = {
    "update-kr-prices-daily": {
        "task": "app.tasks.batch_tasks.update_kr_stock_prices",
        "schedule": crontab(hour=16, minute=5, day_of_week="mon-fri"),
    },
    "update-us-prices-daily": {
        "task": "app.tasks.batch_tasks.update_us_stock_prices",
        "schedule": crontab(hour=6, minute=5, day_of_week="tue-sat"),
    },
    "create-daily-snapshot": {
        "task": "app.tasks.batch_tasks.create_daily_performance_snapshot",
        "schedule": crontab(hour=7, minute=0),
    },
    "refresh-kis-token": {
        "task": "app.tasks.batch_tasks.refresh_kis_token",
        "schedule": crontab(hour=0, minute=0),
    },
}
