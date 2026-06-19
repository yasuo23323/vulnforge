from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Literal
import json
import re


@dataclass
class LLMResponse:
    verdict: Literal["true_positive", "false_positive", "uncertain"]
    confidence: float
    reasoning: str
    severity_reassessment: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0


class BaseLLMClient(ABC):
    def __init__(self, model_name: str, api_key: str):
        self.model_name = model_name
        self.api_key = api_key

    @abstractmethod
    async def analyze(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> LLMResponse:
        pass

    def _parse_json_response(self, raw: str) -> LLMResponse:
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if json_match:
            raw = json_match.group(1)
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return LLMResponse(
                    verdict=data.get("verdict", "uncertain"),
                    confidence=float(data.get("confidence", 0.0)),
                    reasoning=data.get("reasoning", ""),
                    severity_reassessment=data.get("severity_reassessment"),
                )
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        lower = raw.lower()
        if "true_positive" in lower or "true positive" in lower:
            verdict = "true_positive"
        elif "false_positive" in lower or "false positive" in lower:
            verdict = "false_positive"
        else:
            verdict = "uncertain"
        confidence = 0.5
        conf_match = re.search(r"confidence[:\s]+(\d+\.?\d*)", lower)
        if conf_match:
            confidence = min(1.0, max(0.0, float(conf_match.group(1))))
        return LLMResponse(verdict=verdict, confidence=confidence, reasoning=raw[:500])


class OpenAIClient(BaseLLMClient):
    provider_name = "openai"

    def __init__(self, model_name: str, api_key: str, base_url: Optional[str] = None):
        super().__init__(model_name, api_key)
        self.base_url = base_url

    async def analyze(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> LLMResponse:
        from openai import AsyncOpenAI

        kwargs = {"api_key": self.api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url

        client = AsyncOpenAI(**kwargs)
        response = await client.chat.completions.create(
            model=self.model_name,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        result = self._parse_json_response(response.choices[0].message.content or "")
        result.prompt_tokens = response.usage.prompt_tokens if response.usage else 0
        result.completion_tokens = response.usage.completion_tokens if response.usage else 0
        return result


class AnthropicClient(BaseLLMClient):
    provider_name = "anthropic"

    async def analyze(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> LLMResponse:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=self.api_key)
        response = await client.messages.create(
            model=self.model_name,
            temperature=temperature,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        content_text = "".join(block.text for block in response.content if hasattr(block, "text"))
        result = self._parse_json_response(content_text)
        result.prompt_tokens = response.usage.input_tokens if response.usage else 0
        result.completion_tokens = response.usage.output_tokens if response.usage else 0
        return result


def create_llm_client(provider: str, model_name: str, api_key: str, base_url: Optional[str] = None) -> BaseLLMClient:
    if provider == "openai":
        return OpenAIClient(model_name, api_key, base_url=base_url)
    elif provider == "anthropic":
        return AnthropicClient(model_name, api_key)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
