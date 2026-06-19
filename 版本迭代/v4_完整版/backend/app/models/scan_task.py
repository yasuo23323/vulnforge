import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, JSON, Text, ForeignKey, Uuid
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScanTask(Base):
    __tablename__ = "scan_tasks"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    target_url = Column(String(2048), nullable=False)
    target_name = Column(String(255), nullable=True)
    scanners = Column(JSON, nullable=False, default=list)
    status = Column(Enum(ScanStatus, native_enum=False), default=ScanStatus.PENDING, nullable=False)
    parameters = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    findings = relationship("Finding", back_populates="scan_task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ScanTask {self.name} ({self.status.value})>"
