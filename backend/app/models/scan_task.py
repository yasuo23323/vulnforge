import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
import uuid

from app.database import Base

class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ScanTask(Base):
    __tablename__ = "scan_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    target_url = Column(Text, nullable=False)
    target_name = Column(String(200), default="")
    scanners = Column(JSON, default=list)
    parameters = Column(JSON, default=dict)
    status = Column(String(20), default=ScanStatus.PENDING.value)
    error_message = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    findings = relationship("Finding", back_populates="scan_task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ScanTask {self.target_url} [{self.status}]>"
