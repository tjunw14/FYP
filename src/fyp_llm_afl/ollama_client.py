from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class OllamaClient:
    """Small helper for calling a local Ollama chat model."""

    model: str = "qwen2.5-coder:7b"
    base_url: str = "http://localhost:11434"
    timeout: int = 120

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.base_url.rstrip('/')}/api/chat"
        payload: dict[str, Any] = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("content", "").strip()


def extract_json_array(text: str) -> list[Any]:
    """Extract the first JSON array from an LLM response."""
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON array found in LLM response")
    return json.loads(text[start : end + 1])
