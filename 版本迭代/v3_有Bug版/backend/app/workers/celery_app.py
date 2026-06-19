from celery import Celery
from app.config import settings

celery_app = Celery(
    "vulnforge",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


@celery_app.task(bind=True, name="run_scan")
def run_scan(self, scan_id: str):
    """Execute a scan task asynchronously via Celery."""
    import asyncio
    from app.scanner.runner import run_scan_task
    return asyncio.run(run_scan_task(scan_id))
