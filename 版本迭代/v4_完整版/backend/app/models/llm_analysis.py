import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, JSON, Text, ForeignKey, Float, Integer, Uuid
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.finding import Verdict
import enum


class PromptStrategy(str, enum.Enum):
    ZERO_SHOT = "zero_shot"
    FEW_SHOT = "few_shot"
    CHAIN_OF_THOUGHT = "chain_of_thought"


class LLMProvider(str, enum.Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMAnalysis(Base):
    __tablename__ = "llm_analyses"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    finding_id = Column(Uuid, ForeignKey("findings.id", ondelete="CASCADE"), nullable=False)
    provider = Column(Enum(LLMProvider, native_enum=False), nullable=False)
    model_name = Column(String(100), nullable=False)
    strategy = Column(Enum(PromptStrategy, native_enum=False), nullable=False)
    verdict = Column(Enum(Verdict, native_enum=False), nullable=False)
    confidence = Column(Float, nullable=True)
    reasoning = Column(Text, nullable=True)
    severity_reassessment = Column(String(20), nullable=True)
    raw_prompt = Column(Text, nullable=True)
    raw_response = Column(Text, nullable=True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    finding = relationship("Finding", back_populates="llm_analyses")

    def __repr__(self):
        return f"<LLMAnalysis {self.strategy.value}: {self.verdict.value} ({self.confidence:.2f})>"
