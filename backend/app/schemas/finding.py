from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class LLMAnalysisResult(BaseModel):
    id: str = ""
    provider: str = ""
    model_name: str = ""
    strategy: str = ""
    verdict: str = ""
    confidence: float = 0.0
    reasoning: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class FindingResponse(BaseModel):
    id: str = ""
    scan_task_id: str = ""
    scanner_name: str = ""
    vulnerability_type: str = ""
    severity: str = ""
    url: str = ""
    request_data: str = ""
    response_data: str = ""
    raw_evidence: str = ""
    description: str = ""
    extra_data: dict = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    llm_analyses: list[LLMAnalysisResult] = Field(default_factory=list)
    model_config = {"from_attributes": True}

class FindingListResponse(BaseModel):
    items: list[FindingResponse] = Field(default_factory=list)
    total: int = 0