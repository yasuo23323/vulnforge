import asyncio
from celery import Celery

from app.config import settings

celery_app = Celery(
    "vulnforge",
    broker=settings.CELERY_BROKER_URL or settings.REDIS_URL,
    backend=settings.CELERY_RESULT_BACKEND or settings.REDIS_URL,
)
celery_app.conf.update(task_serializer="json", result_serializer="json")


@celery_app.task(bind=True, max_retries=3)
def run_scan(self, scan_id: str):
    from app.scanner.runner import run_scan_task
    asyncio.run(run_scan_task(scan_id))