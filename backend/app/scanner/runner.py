import asyncio
from datetime import datetime
from uuid import UUID

from sqlalchemy import select

from app.database import async_session_factory
from app.models import ScanTask, ScanStatus, Finding, Severity
from app.scanner.orchestrator import ScannerOrchestrator
from app.config import settings


async def run_scan_task(scan_id: str | UUID) -> dict:
    """Execute a scan task with 300s timeout, auto-analyse findings after scan."""
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
                timeout=300
            )

            new_findings = []
            for scanner_name, results in scan_results.items():
                for sr in results:
                    finding = Finding(
                        scan_task_id=task.id,
                        scanner_name=sr.scanner_name,
                        vulnerability_type=sr.vulnerability_type,
                        severity=Severity(sr.severity) if isinstance(sr.severity, str) else sr.severity,
                        url=sr.url,
                        request_data=sr.request_data,
                        response_data=sr.response_data,
                        raw_evidence=sr.raw_evidence,
                        description=sr.description,
                        extra_data=sr.extra_data,
                    )
                    session.add(finding)
                    new_findings.append(finding)
                    findings_count += 1

            session.sync_session.expire_on_commit = False
            await session.commit()

            # Auto-analyse all findings with LLM (concurrent, rate-limited)
            if new_findings and settings.OPENAI_API_KEY:
                from app.llm.client import OpenAIClient
                from app.llm.strategies import LLMAnalyzer, AnalysisStrategy

                client = OpenAIClient(
                    settings.LLM_DEFAULT_MODEL,
                    settings.OPENAI_API_KEY,
                    base_url=settings.OPENAI_BASE_URL
                )
                analyzer = LLMAnalyzer(client)
                sem = asyncio.Semaphore(10)

                async def _analyze_one(finding):
                    async with sem:
                        for strategy in [AnalysisStrategy.ZERO_SHOT, AnalysisStrategy.FEW_SHOT, AnalysisStrategy.CHAIN_OF_THOUGHT]:
                            try:
                                analysis = await analyzer.analyze_finding(finding, strategy)
                                async with async_session_factory() as db:
                                    db.add(analysis)
                                    await db.commit()
                            except Exception as _llm_err:
                                print(f"[LLM] Error: {_llm_err}")

                await asyncio.gather(*[_analyze_one(f) for f in new_findings], return_exceptions=True)

            task.status = ScanStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            await session.commit()
            return {"findings": findings_count, "status": "completed"}

        except asyncio.TimeoutError:
            task.status = ScanStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.error_message = "Scan timed out after 300s"
            await session.commit()
            return {"error": "Timeout", "status": "failed"}

        except Exception as e:
            task.status = ScanStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.error_message = str(e)[:500]
            await session.commit()
            return {"error": str(e), "status": "failed"}


