import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, JSON, Text, ForeignKey, Uuid
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class Severity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Verdict(str, enum.Enum):
    TRUE_POSITIVE = "true_positive"
    FALSE_POSITIVE = "false_positive"
    UNCERTAIN = "uncertain"


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    scan_task_id = Column(Uuid, ForeignKey("scan_tasks.id", ondelete="CASCADE"), nullable=False)
    scanner_name = Column(String(50), nullable=False)
    vulnerability_type = Column(String(100), nullable=False)
    severity = Column(Enum(Severity, native_enum=False), nullable=False)
    url = Column(String(2048), nullable=False)
    request_data = Column(Text, nullable=True)
    response_data = Column(Text, nullable=True)
    raw_evidence = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    scan_task = relationship("ScanTask", back_populates="findings")
    llm_analyses = relationship("LLMAnalysis", back_populates="finding", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Finding {self.vulnerability_type} @ {self.url} ({self.severity.value})>"
