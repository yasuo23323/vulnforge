"""End-to-end test: LLM analysis on a finding, stored in PostgreSQL."""
import sys, asyncio
sys.path.insert(0, r"D:\大论文\backend")

from app.database import async_session_factory, init_db
from app.models import ScanTask, Finding, Severity
from app.llm.client import OpenAIClient
from app.llm.strategies import LLMAnalyzer, AnalysisStrategy
from sqlalchemy import select
from sqlalchemy.orm import selectinload


async def test():
    await init_db()
    async with async_session_factory() as session:
        # Create scan
        scan = ScanTask(name="E2E Test", target_url="http://testphp.vulnweb.com", scanners=["nuclei"])
        session.add(scan)
        await session.commit()

        # Create a finding
        finding = Finding(
            scan_task_id=scan.id,
            scanner_name="nuclei",
            vulnerability_type="sql_injection",
            severity=Severity.HIGH,
            url="http://testphp.vulnweb.com/products.php?cat=1",
            request_data="GET /products.php?cat=1 HTTP/1.1",
            response_data="HTTP/1.1 200 OK...MySQL Error: syntax error...",
            raw_evidence="MySQL error detected in response",
            description="SQL injection in cat parameter",
        )
        session.add(finding)
        await session.commit()
        print(f"1. Finding created: {str(finding.id)[:8]}...")

        # Run LLM analysis (Zero-shot)
        async def get_key():
            with open(r"D:\大论文\backend\.env") as f:
                for line in f:
                    if line.startswith("OPENAI_API_KEY="):
                        return line.strip().split("=", 1)[1]
            return ""

        api_key = await get_key()
        client = OpenAIClient("deepseek-chat", api_key, base_url="https://api.deepseek.com")
        analyzer = LLMAnalyzer(client)
        analysis = await analyzer.analyze_finding(finding, AnalysisStrategy.ZERO_SHOT)
        analysis.finding_id = finding.id
        session.add(analysis)
        await session.commit()
        await session.refresh(analysis)

        # Verify
        result = await session.execute(
            select(Finding).options(selectinload(Finding.llm_analyses)).where(Finding.id == finding.id)
        )
        loaded = result.unique().scalar_one()
        a = loaded.llm_analyses[0]
        print(f"2. Analyses stored: {len(loaded.llm_analyses)}")
        print(f"3. Verdict: {a.verdict.value}")
        print(f"4. Confidence: {a.confidence}")
        print(f"5. Reasoning: {a.reasoning[:100]}...")
        print(f"6. Latency: {a.latency_ms}ms")
        print("--- E2E TEST PASSED ---")

        # Cleanup
        await session.delete(loaded)
        await session.delete(scan)
        await session.commit()
        print("Test data cleaned up")

asyncio.run(test())
