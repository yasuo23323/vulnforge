import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Enum, Float, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship
import uuid

from app.database import Base

class LLMProvider(str, enum.Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

class PromptStrategy(str, enum.Enum):
    ZERO_SHOT = "zero_shot"
    FEW_SHOT = "few_shot"
    CHAIN_OF_THOUGHT = "chain_of_thought"

class LLMAnalysis(Base):
    __tablename__ = "llm_analyses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    finding_id = Column(String(36), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(20), default=LLMProvider.OPENAI.value)
    model_name = Column(String(100), default="")
    strategy = Column(String(20), default=PromptStrategy.ZERO_SHOT.value)
    verdict = Column(String(20), default="")
    confidence = Column(Float, default=0.0)
    reasoning = Column(Text, default="")
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    raw_response = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    finding = relationship("Finding", back_populates="llm_analyses")

    def __repr__(self):
        return f"<LLMAnalysis {self.verdict} ({self.confidence:.2f})>"
