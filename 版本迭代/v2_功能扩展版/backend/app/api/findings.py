from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Optional

from app.database import get_db
from app.models import Finding, LLMAnalysis, Verdict
from app.schemas.finding import FindingResponse, FindingListResponse, LLMAnalysisResult
from app.llm.client import OpenAIClient, AnthropicClient
from app.llm.strategies import LLMAnalyzer, AnalysisStrategy
from app.config import settings

router = APIRouter(prefix="/api/findings", tags=["findings"])


@router.get("", response_model=FindingListResponse)
async def list_findings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    scan_task_id: Optional[UUID] = None,
    scanner_name: Optional[str] = None,
    vulnerability_type: Optional[str] = None,
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Finding).options(selectinload(Finding.llm_analyses))
    count_query = select(func.count(Finding.id))

    if scan_task_id:
        query = query.where(Finding.scan_task_id == scan_task_id)
        count_query = count_query.where(Finding.scan_task_id == scan_task_id)
    if scanner_name:
        query = query.where(Finding.scanner_name == scanner_name)
        count_query = count_query.where(Finding.scanner_name == scanner_name)
    if vulnerability_type:
        query = query.where(Finding.vulnerability_type == vulnerability_type)
        count_query = count_query.where(Finding.vulnerability_type == vulnerability_type)
    if severity:
        query = query.where(Finding.severity == severity)
        count_query = count_query.where(Finding.severity == severity)

    query = query.order_by(Finding.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    findings = result.unique().scalars().all()

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    items = [_finding_to_response(f) for f in findings]
    return FindingListResponse(items=items, total=total)


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(finding_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Finding).options(selectinload(Finding.llm_analyses)).where(Finding.id == finding_id)
    )
    finding = result.unique().scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return _finding_to_response(finding)


@router.post("/{finding_id}/analyze", response_model=LLMAnalysisResult)
async def analyze_finding(
    finding_id: UUID,
    strategy: str = Query("zero_shot", description="Analysis strategy: zero_shot, few_shot, chain_of_thought"),
    db: AsyncSession = Depends(get_db),
):
    """Run LLM analysis on a finding using the specified prompt strategy."""
    result = await db.execute(
        select(Finding).options(selectinload(Finding.llm_analyses)).where(Finding.id == finding_id)
    )
    finding = result.unique().scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    # Validate strategy
    strategy_map = {
        "zero_shot": AnalysisStrategy.ZERO_SHOT,
        "few_shot": AnalysisStrategy.FEW_SHOT,
        "chain_of_thought": AnalysisStrategy.CHAIN_OF_THOUGHT,
    }
    ast = strategy_map.get(strategy)
    if not ast:
        raise HTTPException(status_code=400, detail=f"Invalid strategy: {strategy}")

    # Create LLM client
    api_key = settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY
    if not api_key:
        raise HTTPException(status_code=400, detail="No LLM API key configured")

    provider = settings.LLM_DEFAULT_PROVIDER
    model = settings.LLM_DEFAULT_MODEL

    if provider == "openai":
        client = OpenAIClient(model, api_key, base_url=settings.OPENAI_BASE_URL)
    elif provider == "anthropic":
        client = AnthropicClient(model, api_key)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    # Run analysis
    import asyncio
    analyzer = LLMAnalyzer(client)
    analysis = await analyzer.analyze_finding(finding, ast)

    # Store result
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    return LLMAnalysisResult(
        id=analysis.id,
        provider=analysis.provider,
        model_name=analysis.model_name,
        strategy=analysis.strategy.value,
        verdict=analysis.verdict.value,
        confidence=analysis.confidence,
        reasoning=analysis.reasoning,
        severity_reassessment=analysis.severity_reassessment,
        prompt_tokens=analysis.prompt_tokens,
        completion_tokens=analysis.completion_tokens,
        latency_ms=analysis.latency_ms,
        created_at=analysis.created_at,
    )


def _finding_to_response(finding: Finding) -> FindingResponse:
    analyses = []
    for a in (finding.llm_analyses or []):
        analyses.append(LLMAnalysisResult(
            id=a.id, provider=a.provider, model_name=a.model_name,
            strategy=a.strategy.value, verdict=a.verdict.value,
            confidence=a.confidence, reasoning=a.reasoning,
            severity_reassessment=a.severity_reassessment,
            prompt_tokens=a.prompt_tokens, completion_tokens=a.completion_tokens,
            latency_ms=a.latency_ms, created_at=a.created_at,
        ))
    return FindingResponse(
        id=finding.id, scan_task_id=finding.scan_task_id,
        scanner_name=finding.scanner_name, vulnerability_type=finding.vulnerability_type,
        severity=finding.severity.value, url=finding.url,
        request_data=finding.request_data, response_data=finding.response_data,
        raw_evidence=finding.raw_evidence, description=finding.description,
        extra_data=finding.extra_data, created_at=finding.created_at,
        llm_analyses=analyses,
    )
