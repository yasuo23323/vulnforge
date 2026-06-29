from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional

from app.database import get_db
from app.models import Finding, LLMAnalysis
from app.schemas.finding import FindingResponse, FindingListResponse, LLMAnalysisResult
from app.llm.strategies import LLMAnalyzer, AnalysisStrategy

router = APIRouter(prefix="/api/findings", tags=["findings"])


@router.get("", response_model=FindingListResponse)
async def list_findings(
    scan_task_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = select(Finding)
    if scan_task_id:
        q = q.where(Finding.scan_task_id == scan_task_id)
    q = q.order_by(desc(Finding.created_at)).offset((page - 1) * page_size).limit(page_size)

    total_q = select(func.count(Finding.id))
    if scan_task_id:
        total_q = total_q.where(Finding.scan_task_id == scan_task_id)

    total = (await db.execute(total_q)).scalar() or 0
    findings = (await db.execute(q)).scalars().all()

    items = []
    for f in findings:
        analyses = []
        for a in (f.llm_analyses or []):
            analyses.append(LLMAnalysisResult(
                id=a.id, provider=a.provider, model_name=a.model_name,
                strategy=a.strategy, verdict=a.verdict, confidence=a.confidence,
                reasoning=a.reasoning, prompt_tokens=a.prompt_tokens,
                completion_tokens=a.completion_tokens, latency_ms=a.latency_ms,
                created_at=a.created_at,
            ))
        items.append(FindingResponse(
            id=f.id, scan_task_id=f.scan_task_id,
            scanner_name=f.scanner_name, vulnerability_type=f.vulnerability_type,
            severity=f.severity, url=f.url, request_data=f.request_data,
            response_data=f.response_data, raw_evidence=f.raw_evidence,
            description=f.description, extra_data=f.extra_data or {},
            created_at=f.created_at, llm_analyses=analyses,
        ))

    return FindingListResponse(items=items, total=total)


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(finding_id: str, db: AsyncSession = Depends(get_db)):
    finding = await db.get(Finding, finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding


@router.post("/{finding_id}/analyze", response_model=LLMAnalysisResult)
async def analyze_finding(
    finding_id: str,
    strategy: str = Query("zero_shot", description="Analysis strategy: zero_shot, few_shot, chain_of_thought"),
    db: AsyncSession = Depends(get_db),
):
    finding = await db.get(Finding, finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    analyzer = LLMAnalyzer()
    result = await analyzer.analyze_finding(finding, strategy)
    if not result:
        raise HTTPException(status_code=400, detail="No LLM API key configured")

    result.finding_id = finding_id
    db.add(result)
    await db.commit()
    await db.refresh(result)

    return LLMAnalysisResult(
        id=result.id, provider=result.provider, model_name=result.model_name,
        strategy=result.strategy, verdict=result.verdict, confidence=result.confidence,
        reasoning=result.reasoning, prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens, latency_ms=result.latency_ms,
        created_at=result.created_at,
    )