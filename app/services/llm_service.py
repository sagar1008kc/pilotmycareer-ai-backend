"""LLM provider abstraction.

Goals:
- OpenAI is the primary provider.
- If no ``OPENAI_API_KEY`` is set (or ``LLM_PROVIDER=mock``), fall back to a deterministic
  mock provider so the whole API works end-to-end with no key and no cost.
- Grok / Gemini / Claude are stubbed as future providers.

Agents call :func:`generate_json`, passing a deterministic ``fallback`` value that is returned
whenever the active provider is the mock provider or when JSON parsing fails. This keeps every
endpoint functional and predictable regardless of LLM availability.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger
from app.models.common import Usage

logger = get_logger("app.services.llm")


@dataclass
class LLMResult:
    text: str
    provider: str
    model: str
    usage: Usage = field(default_factory=Usage)


class LLMProvider:
    name: str = "base"

    @property
    def is_mock(self) -> bool:
        return False

    def complete(self, system: str, user: str, *, json_mode: bool = False) -> LLMResult:
        raise NotImplementedError


class MockProvider(LLMProvider):
    name = "mock"

    @property
    def is_mock(self) -> bool:
        return True

    def complete(self, system: str, user: str, *, json_mode: bool = False) -> LLMResult:
        # The caller supplies deterministic fallbacks; mock text is informational only.
        return LLMResult(
            text="[mock] LLM disabled (no OPENAI_API_KEY). Returning deterministic output.",
            provider=self.name,
            model="mock-1",
        )


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model

    def complete(self, system: str, user: str, *, json_mode: bool = False) -> LLMResult:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.4,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        resp = self._client.chat.completions.create(**kwargs)
        text = resp.choices[0].message.content or ""
        usage = Usage()
        if resp.usage is not None:
            usage = Usage(
                prompt_tokens=resp.usage.prompt_tokens or 0,
                completion_tokens=resp.usage.completion_tokens or 0,
                total_tokens=resp.usage.total_tokens or 0,
            )
        return LLMResult(text=text, provider=self.name, model=self._model, usage=usage)


class _NotImplementedProvider(LLMProvider):
    """Placeholder for future providers (Grok / Gemini / Claude)."""

    def __init__(self, name: str) -> None:
        self.name = name

    def complete(self, system: str, user: str, *, json_mode: bool = False) -> LLMResult:
        raise NotImplementedError(f"Provider '{self.name}' is not implemented yet")


def get_provider() -> LLMProvider:
    """Resolve the active provider, defaulting to mock when unusable."""
    provider = settings.llm_provider
    if provider == "openai":
        if not settings.has_openai:
            logger.info("No OPENAI_API_KEY set; using mock provider")
            return MockProvider()
        return OpenAIProvider()
    if provider == "mock":
        return MockProvider()
    if provider in {"grok", "gemini", "claude"}:
        # Not implemented yet — fall back to mock to keep the API functional.
        logger.info("Provider %s not implemented; using mock provider", provider)
        return MockProvider()
    return MockProvider()


def _extract_json(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    cleaned = text.strip()
    if "```" in cleaned:
        # Strip code fences if the model wrapped the JSON.
        cleaned = cleaned.split("```", 2)
        cleaned = cleaned[1] if len(cleaned) > 1 else text
        cleaned = cleaned.removeprefix("json").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if 0 <= start < end:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                return None
    return None


def generate_json(
    system: str,
    user: str,
    *,
    fallback: dict[str, Any],
) -> tuple[dict[str, Any], LLMResult]:
    """Generate structured JSON, returning ``fallback`` when the LLM is unavailable.

    Always returns a ``(data, result)`` tuple. ``data`` merges the LLM output over the
    fallback so missing keys are still populated deterministically.
    """
    provider = get_provider()
    if provider.is_mock:
        return dict(fallback), provider.complete(system, user)

    try:
        result = provider.complete(system, user, json_mode=True)
    except Exception:
        logger.exception("LLM call failed; using fallback", extra={"provider": provider.name})
        return dict(fallback), LLMResult(text="", provider=provider.name, model="error")

    parsed = _extract_json(result.text)
    if not parsed:
        return dict(fallback), result
    merged = {**fallback, **parsed}
    return merged, result


def generate_text(system: str, user: str, *, fallback: str) -> tuple[str, LLMResult]:
    """Generate free-form text, returning ``fallback`` when the LLM is unavailable."""
    provider = get_provider()
    if provider.is_mock:
        return fallback, provider.complete(system, user)
    try:
        result = provider.complete(system, user)
    except Exception:
        logger.exception("LLM call failed; using fallback", extra={"provider": provider.name})
        return fallback, LLMResult(text="", provider=provider.name, model="error")
    return (result.text or fallback), result
