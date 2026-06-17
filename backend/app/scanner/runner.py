import asyncio
from datetime import datetime
from uuid import UUID

from sqlalchemy import select

from app.database import async_session_factory
from app.models import ScanTask, ScanStatus, Finding
from app.scanner.orchestrator import ScannerOrchestrator


async def run_scan_task(scan_id: str | UUID) -> dict:
    """Execute a scan task with 180s timeout."""
    async with async_session_factory() as session:
        result = await session.execute(select(ScanTask).where(ScanTask.id == scan_id))
        task = result.scalar_one_or_none()
        if not task:
            return {"error": "Scan not found"}

        task.status = ScanStatus.RUNNING
        task.started_at = datetime.utcnow()
        await session.commit()

        findings_count = 0
        try:
            orch = ScannerOrchestrator()
            scan_results = await asyncio.wait_for(
                orch.run_scanners(task.target_url, task.scanners, **(task.parameters or {})),
                timeout=180
            )

            for scanner_name, results in scan_results.items():
                for sr in results:
                    finding = Finding(
                        scan_task_id=task.id,
                        scanner_name=sr.scanner_name,
                        vulnerability_type=sr.vulnerability_type,
                        severity=sr.severity,
                        url=sr.url,
                        request_data=sr.request_data,
                        response_data=sr.response_data,
                        raw_evidence=sr.raw_evidence,
                        description=sr.description,
                        extra_data=sr.extra_data,
                    )
                    session.add(finding)
                    findings_count += 1

            task.status = ScanStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            await session.commit()
            return {"findings": findings_count, "status": "completed"}

        except asyncio.TimeoutError:
            task.status = ScanStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.error_message = "Scan timed out after 180s"
            await session.commit()
            return {"error": "Timeout", "status": "failed"}

        except Exception as e:
            task.status = ScanStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.error_message = str(e)[:500]
            await session.commit()
            return {"error": str(e), "status": "failed"}

