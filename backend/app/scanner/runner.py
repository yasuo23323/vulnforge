import asyncio
from datetime import datetime, timezone

from app.database import async_session_factory
from app.models import ScanTask, Finding, ScanStatus
from app.scanner.orchestrator import ScannerOrchestrator


async def run_scan_task(scan_id: str) -> None:
    orchestrator = ScannerOrchestrator()

    async with async_session_factory() as session:
        scan = await session.get(ScanTask, scan_id)
        if not scan:
            return

        scan.status = ScanStatus.RUNNING.value
        scan.started_at = datetime.now(timezone.utc)
        await session.commit()

        try:
            results = await asyncio.wait_for(
                orchestrator.execute_all(scan.target_url),
                timeout=180,
            )

            for result in results:
                finding = Finding(
                    scan_task_id=scan.id,
                    scanner_name=result.scanner_name,
                    vulnerability_type=result.vulnerability_type,
                    severity=result.severity,
                    url=result.url,
                    request_data=result.request_data or "",
                    response_data=result.response_data or "",
                    raw_evidence=result.raw_evidence or result.raw_output,
                    description=result.description,
                    extra_data=result.extra_data,
                )
                session.add(finding)

            scan.status = ScanStatus.COMPLETED.value

        except asyncio.TimeoutError:
            scan.status = ScanStatus.FAILED.value
            scan.error_message = "Scan timed out after 180 seconds"
        except Exception as e:
            scan.status = ScanStatus.FAILED.value
            scan.error_message = str(e)

        scan.completed_at = datetime.now(timezone.utc)
        await session.commit()