import enum
import time
from typing import Optional

from app.models.finding import Finding, Verdict
from app.models.llm_analysis import LLMAnalysis, LLMProvider, PromptStrategy
from app.llm.client import BaseLLMClient, OpenAIClient, AnthropicClient, LLMResponse
from app.llm.prompts import PromptBuilder
from app.config import settings


class AnalysisStrategy(str, enum.Enum):
    ZERO_SHOT = "zero_shot"
    FEW_SHOT = "few_shot"
    CHAIN_OF_THOUGHT = "chain_of_thought"


class LLMAnalyzer:

    def __init__(self, provider_name: str = "", api_key: str = ""):
        self.provider_name = provider_name or settings.LLM_DEFAULT_PROVIDER
        self.api_key = api_key or self._get_api_key()

    def _get_api_key(self) -> str:
        if self.provider_name == "anthropic":
            return settings.ANTHROPIC_API_KEY
        return settings.OPENAI_API_KEY

    def _build_client(self) -> Optional[BaseLLMClient]:
        if self.provider_name == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                return None
            return AnthropicClient(api_key=settings.ANTHROPIC_API_KEY)
        else:
            if not settings.OPENAI_API_KEY:
                return None
            return OpenAIClient(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL,
                model=settings.LLM_DEFAULT_MODEL,
            )

    def _build_prompts(self, finding: Finding, strategy: str) -> tuple[str, str]:
        if strategy == AnalysisStrategy.CHAIN_OF_THOUGHT.value:
            return PromptBuilder.build_chain_of_thought(finding)
        elif strategy == AnalysisStrategy.FEW_SHOT.value:
            return PromptBuilder.build_few_shot(finding)
        return PromptBuilder.build_zero_shot(finding)

    async def analyze_finding(self, finding: Finding,
                              strategy: str = AnalysisStrategy.ZERO_SHOT.value) -> Optional[LLMAnalysis]:
        client = self._build_client()
        if not client:
            return None

        system_prompt, user_prompt = self._build_prompts(finding, strategy)
        start = time.monotonic()

        try:
            response: LLMResponse = await client.analyze(system_prompt, user_prompt)
        except Exception as e:
            return LLMAnalysis(
                finding_id=finding.id,
                provider=self.provider_name,
                model_name=settings.LLM_DEFAULT_MODEL,
                strategy=strategy,
                verdict=Verdict.UNCERTAIN.value,
                reasoning=f"LLM API error: {e}",
            )

        elapsed = int((time.monotonic() - start) * 1000)
        return LLMAnalysis(
            finding_id=finding.id,
            provider=self.provider_name,
            model_name=response.model_name or settings.LLM_DEFAULT_MODEL,
            strategy=strategy,
            verdict=response.verdict or Verdict.UNCERTAIN.value,
            confidence=response.confidence,
            reasoning=response.reasoning,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            latency_ms=elapsed,
        )