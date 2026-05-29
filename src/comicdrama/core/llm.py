from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class LLMError(RuntimeError):
    """Raised when an LLM provider cannot return a usable structured result."""


@dataclass(frozen=True)
class LLMSettings:
    api_base_url: str
    api_key: str
    model: str
    timeout_seconds: int = 90
    temperature: float = 0.2
    max_output_tokens: int = 4096

    @classmethod
    def from_env(cls) -> Optional["LLMSettings"]:
        api_base_url = os.getenv("LLM_API_BASE_URL") or os.getenv("OPENAI_BASE_URL")
        api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        model = os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL")
        if not (api_base_url and api_key and model):
            return None
        return cls(
            api_base_url=api_base_url.rstrip("/"),
            api_key=api_key,
            model=model,
            timeout_seconds=int(os.getenv("LLM_TIMEOUT_SECONDS", "90")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
            max_output_tokens=int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "4096")),
        )


class LLMClient:
    """Small OpenAI-compatible chat completions client with JSON-only output."""

    def __init__(self, settings: LLMSettings):
        self.settings = settings

    @classmethod
    def from_env(cls) -> Optional["LLMClient"]:
        settings = LLMSettings.from_env()
        return cls(settings) if settings else None

    def structured_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema_name: str,
        schema: Dict[str, Any],
    ) -> Dict[str, Any]:
        payload = {
            "model": self.settings.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.settings.temperature,
            "max_tokens": self.settings.max_output_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "schema": schema,
                    "strict": True,
                },
            },
        }
        response = self._post_json("/chat/completions", payload)
        content = _extract_message_content(response)
        return _parse_json_object(content)

    def _post_json(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.settings.api_base_url}{path}"
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = Request(
            url,
            data=raw,
            headers={
                "Authorization": f"Bearer {self.settings.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.settings.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise LLMError(f"LLM provider returned HTTP {exc.code}: {detail[:500]}") from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise LLMError(f"LLM provider request failed: {exc}") from exc


def load_prompt(name: str) -> str:
    prompt_path = Path(__file__).resolve().parents[3] / "prompts" / name
    return prompt_path.read_text(encoding="utf-8")


def _extract_message_content(response: Dict[str, Any]) -> str:
    choices = response.get("choices") or []
    if not choices:
        raise LLMError("LLM provider returned no choices.")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = [item.get("text", "") for item in content if isinstance(item, dict)]
        return "\n".join(part for part in text_parts if part)
    raise LLMError("LLM provider returned an unsupported message content shape.")


def _parse_json_object(content: str) -> Dict[str, Any]:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise LLMError(f"LLM provider did not return valid JSON: {content[:500]}") from exc
    if not isinstance(parsed, dict):
        raise LLMError("LLM provider returned JSON, but not a JSON object.")
    return parsed
