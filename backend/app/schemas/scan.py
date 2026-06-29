from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class ScanCreate(BaseModel):
    target_url: str
    target_name: str = ""
    scanners: list[str] = Field(default_factory=lambda: ["nuclei", "dalfox", "ffuf", "sqlmap"])
    parameters: dict = Field(default_factory=dict)

class ScanUpdate(BaseModel):
    status: Optional[str] = None
    error_message: Optional[str] = None

class ScanResponse(BaseModel):
    id: str = ""
    target_url: str = ""
    target_name: str = ""
    scanners: list[str] = Field(default_factory=list)
    parameters: dict = Field(default_factory=dict)
    status: str = ""
    error_message: str = ""
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    findings_count: int = 0
    model_config = {"from_attributes": True}

class ScanListResponse(BaseModel):
    items: list[ScanResponse] = Field(default_factory=list)
    total: int = 0