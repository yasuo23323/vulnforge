from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID


# ─── Scan Schemas ───

class ScanCreate(BaseModel):
    name: str = Field(..., max_length=255)
    target_url: str = Field(..., max_length=2048)
    target_name: Optional[str] = Field(None, max_length=255)
    scanners: list[str] = Field(default_factory=lambda: ["nuclei"])
    parameters: Optional[dict] = None


class ScanUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[Literal["pending", "running", "completed", "failed", "cancelled"]] = None


class ScanResponse(BaseModel):
    id: UUID
    name: str
    target_url: str
    target_name: Optional[str]
    scanners: list[str]
    status: str
    parameters: Optional[dict]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    findings_count: int = 0

    model_config = {"from_attributes": True}


class ScanListResponse(BaseModel):
    items: list[ScanResponse]
    total: int
