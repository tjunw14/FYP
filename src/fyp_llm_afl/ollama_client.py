from __future__ import annotations

import ast
import json
import re
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
            "format": "json",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("content", "").strip()


def _normalise_seed_list(value: Any) -> list[str]:
    """Convert common LLM JSON shapes into a clean list of hex strings."""
    if isinstance(value, list):
        items = value
    elif isinstance(value, dict):
        for key in ("seeds", "inputs", "hex_strings", "seed_inputs"):
            if isinstance(value.get(key), list):
                items = value[key]
                break
        else:
            items = list(value.values())
    else:
        raise ValueError("LLM response did not contain a list or dictionary")

    seeds: list[str] = []
    for item in items:
        if isinstance(item, str):
            candidate = item
        elif isinstance(item, dict):
            candidate = str(
                item.get("hex")
                or item.get("seed")
                or item.get("input")
                or item.get("data")
                or ""
            )
        else:
            candidate = str(item)

        candidate = candidate.strip().replace("0x", "")
        candidate = re.sub(r"[^0-9a-fA-F]", "", candidate)
        if candidate:
            seeds.append(candidate)

    if not seeds:
        raise ValueError("No usable hex seeds found in LLM response")
    return seeds


def extract_json_array(text: str) -> list[str]:
    """Extract seed hex strings from strict or messy LLM output."""
    errors: list[str] = []

    # 1. Try direct JSON. With Ollama format=json this is usually the best path.
    try:
        return _normalise_seed_list(json.loads(text))
    except Exception as exc:  # noqa: BLE001 - keep original parsing error for debugging
        errors.append(f"direct json: {exc}")

    # 2. Try the first JSON-looking object or array.
    for opening, closing in (("[", "]"), ("{", "}")):
        start = text.find(opening)
        end = text.rfind(closing)
        if start != -1 and end != -1 and end > start:
            fragment = text[start : end + 1]
            try:
                return _normalise_seed_list(json.loads(fragment))
            except Exception as exc:  # noqa: BLE001
                errors.append(f"fragment json: {exc}")
            try:
                return _normalise_seed_list(ast.literal_eval(fragment))
            except Exception as exc:  # noqa: BLE001
                errors.append(f"fragment literal: {exc}")

    # 3. Last resort: collect hex-looking strings from the response.
    candidates = re.findall(r"(?:0x)?[0-9a-fA-F]{4,}", text)
    candidates = [re.sub(r"[^0-9a-fA-F]", "", c.replace("0x", "")) for c in candidates]
    if candidates:
        return candidates

    raise ValueError(
        "Could not parse LLM response into seed inputs. "
        f"Parsing attempts: {'; '.join(errors)}. Raw response: {text[:500]!r}"
    )
