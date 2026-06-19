import asyncio
from datetime import datetime
from sqlalchemy import select
from app.database import async_session_factory
from app.models import ScanTask, ScanStatus, Finding
from app.scanner.orchestrator import ScannerOrchestrator

async def run_scan_task(scan_id):
    async with async_session_factory() as session:
        r = await session.execute(select(ScanTask).where(ScanTask.id == scan_id))
        t = r.scalar_one_or_none()
        if not t: return {"error": "not found"}
        t.status = ScanStatus.RUNNING
        t.started_at = datetime.utcnow()
        await session.commit()
        try:
            # BUG: no timeout - scan can hang forever
            results = await ScannerOrchestrator().run_scanners(t.target_url, t.scanners)
            for s, find in results.items():
                for sr in find:
                    session.add(Finding(scan_task_id=t.id, scanner_name=sr.scanner_name,
                        vulnerability_type=sr.vulnerability_type, severity=sr.severity, url=sr.url))
            t.status = ScanStatus.COMPLETED
            t.completed_at = datetime.utcnow()
            await session.commit()
        except Exception as e:
            t.status = ScanStatus.FAILED
            t.error_message = str(e)[:500]
            await session.commit()