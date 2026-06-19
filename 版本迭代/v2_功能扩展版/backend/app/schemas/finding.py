from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class LLMAnalysisResult(BaseModel):
    id: UUID
    provider: str
    model_name: str
    strategy: str
    verdict: str
    confidence: Optional[float]
    reasoning: Optional[str]
    severity_reassessment: Optional[str]
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    latency_ms: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class FindingResponse(BaseModel):
    id: UUID
    scan_task_id: UUID
    scanner_name: str
    vulnerability_type: str
    severity: str
    url: str
    request_data: Optional[str]
    response_data: Optional[str]
    raw_evidence: Optional[str]
    description: Optional[str]
    extra_data: Optional[dict]
    created_at: datetime
    llm_analyses: list[LLMAnalysisResult] = []

    model_config = {"from_attributes": True}


class FindingListResponse(BaseModel):
    items: list[FindingResponse]
    total: int
