import json
import re
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic


@dataclass
class LLMResponse:
    content: str = ""
    verdict: str = ""
    confidence: float = 0.0
    reasoning: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model_name: str = ""


def _parse_json_response(text: str) -> dict:
    text = text.strip()
    pattern = r"`(?:json)?\s*(\{.*?\})\s*`"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        text = match.group(1)
    brace_start = text.find("{")
    if brace_start >= 0:
        text = text[brace_start:]
        brace_end = text.rfind("}")
        if brace_end >= 0:
            text = text[:brace_end + 1]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    result = {}
    conf_match = re.search(r"confidence[\s:]+(\d+\.?\d*)", text, re.IGNORECASE)
    if conf_match:
        result["confidence"] = float(conf_match.group(1))
    if "false positive" in text.lower():
        result["verdict"] = "false_positive"
    return result


class BaseLLMClient(ABC):
    @abstractmethod
    async def analyze(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        ...


class OpenAIClient(BaseLLMClient):
    def __init__(self, api_key: str, base_url: str = "", model: str = "deepseek-chat"):
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = AsyncOpenAI(**kwargs)
        self.model = model

    async def analyze(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.1,
        )
        choice = resp.choices[0]
        content = choice.message.content or ""
        parsed = _parse_json_response(content)
        return LLMResponse(
            content=content,
            verdict=parsed.get("verdict", ""),
            confidence=parsed.get("confidence", 0.0),
            reasoning=content,
            prompt_tokens=resp.usage.prompt_tokens if resp.usage else 0,
            completion_tokens=resp.usage.completion_tokens if resp.usage else 0,
            model_name=self.model,
        )


class AnthropicClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def analyze(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        resp = await self.client.messages.create(
            model=self.model,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            max_tokens=1024,
        )
        content = "".join(b.text for b in resp.content if hasattr(b, "text"))
        parsed = _parse_json_response(content)
        return LLMResponse(
            content=content,
            verdict=parsed.get("verdict", ""),
            confidence=parsed.get("confidence", 0.0),
            reasoning=content,
            prompt_tokens=resp.usage.input_tokens if resp.usage else 0,
            completion_tokens=resp.usage.output_tokens if resp.usage else 0,
            model_name=self.model,
        )