import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
import uuid

from app.database import Base

class Severity(str, enum.Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Verdict(str, enum.Enum):
    TRUE_POSITIVE = "true_positive"
    FALSE_POSITIVE = "false_positive"
    UNCERTAIN = "uncertain"

class Finding(Base):
    __tablename__ = "findings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_task_id = Column(String(36), ForeignKey("scan_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    scanner_name = Column(String(50), nullable=False)
    vulnerability_type = Column(String(200), default="")
    severity = Column(String(20), default=Severity.MEDIUM.value)
    url = Column(Text, default="")
    request_data = Column(Text, default="")
    response_data = Column(Text, default="")
    raw_evidence = Column(Text, default="")
    description = Column(Text, default="")
    extra_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    scan_task = relationship("ScanTask", back_populates="findings")
    llm_analyses = relationship("LLMAnalysis", back_populates="finding", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Finding {self.scanner_name}:{self.vulnerability_type} [{self.severity}]>"
