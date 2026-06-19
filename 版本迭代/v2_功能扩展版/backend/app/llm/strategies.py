from enum import Enum
from typing import Optional
from app.llm.client import BaseLLMClient, LLMResponse
from app.llm.prompts import PromptBuilder
from app.models import Finding, LLMAnalysis, Verdict, PromptStrategy as PromptStrategyEnum
from app.scanner.base import ScanResult
import time


class AnalysisStrategy(Enum):
    ZERO_SHOT = "zero_shot"
    FEW_SHOT = "few_shot"
    CHAIN_OF_THOUGHT = "chain_of_thought"


class LLMAnalyzer:
    """Orchestrates LLM-based analysis of scanner findings."""

    def __init__(self, client: BaseLLMClient):
        self.client = client
        self.prompt_builder = PromptBuilder()

    async def analyze_finding(
        self,
        finding: Finding,
        strategy: AnalysisStrategy = AnalysisStrategy.ZERO_SHOT,
    ) -> LLMAnalysis:
        """Run a single finding through LLM analysis with the given strategy."""
        system_prompt, user_prompt = self._build_prompts(finding, strategy)

        start_time = time.monotonic()
        try:
            response = await self.client.analyze(system_prompt, user_prompt)
            latency = int((time.monotonic() - start_time) * 1000)
        except Exception as e:
            latency = int((time.monotonic() - start_time) * 1000)
            response = LLMResponse(
                verdict="uncertain",
                confidence=0.0,
                reasoning=f"LLM API error: {str(e)}",
            )

        return LLMAnalysis(
            finding_id=finding.id,
            provider=self.client.provider_name if hasattr(self.client, 'provider_name') else "unknown",
            model_name=self.client.model_name,
            strategy=PromptStrategyEnum(strategy.value),
            verdict=Verdict(response.verdict),
            confidence=response.confidence,
            reasoning=response.reasoning,
            severity_reassessment=response.severity_reassessment,
            raw_prompt=f"System: {system_prompt}\n\nUser: {user_prompt}",
            raw_response=str(response),
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            latency_ms=latency,
        )

    async def analyze_scan_result(
        self,
        result: ScanResult,
        strategy: AnalysisStrategy = AnalysisStrategy.ZERO_SHOT,
    ) -> LLMResponse:
        """Analyze a raw ScanResult directly (before persistence)."""
        system, user = self._build_prompts_from_scan_result(result, strategy)
        return await self.client.analyze(system, user)

    def _build_prompts(self, finding: Finding, strategy: AnalysisStrategy):
        builders = {
            AnalysisStrategy.ZERO_SHOT: self.prompt_builder.build_zero_shot,
            AnalysisStrategy.FEW_SHOT: self.prompt_builder.build_few_shot,
            AnalysisStrategy.CHAIN_OF_THOUGHT: self.prompt_builder.build_chain_of_thought,
        }
        builder = builders.get(strategy, self.prompt_builder.build_zero_shot)
        return builder(finding)

    def _build_prompts_from_scan_result(self, result: ScanResult, strategy: AnalysisStrategy):
        """Build prompts from a ScanResult dataclass."""
        class MockFinding:
            class MockSeverity:
                value = result.severity
            scanner_name = result.scanner_name
            vulnerability_type = result.vulnerability_type
            severity = MockSeverity()
            url = result.url
            description = result.description
            raw_evidence = result.raw_evidence
            request_data = result.request_data
            response_data = result.response_data

        builders = {
            AnalysisStrategy.ZERO_SHOT: self.prompt_builder.build_zero_shot,
            AnalysisStrategy.FEW_SHOT: self.prompt_builder.build_few_shot,
            AnalysisStrategy.CHAIN_OF_THOUGHT: self.prompt_builder.build_chain_of_thought,
        }
        builder = builders.get(strategy, self.prompt_builder.build_zero_shot)
        return builder(MockFinding())
