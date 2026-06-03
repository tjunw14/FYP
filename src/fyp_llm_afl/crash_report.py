from __future__ import annotations

import argparse
import os
from pathlib import Path

from .ollama_client import OllamaClient


SYSTEM_PROMPT = """You are assisting with defensive vulnerability analysis for a university FYP.
Analyse fuzzing crash artifacts at a high level.
Do not provide exploit instructions.
Focus on likely root cause, affected parser logic, reproducibility steps, impact, and suggested secure coding fixes.
"""


def read_crash_files(crash_dir: Path, limit: int) -> str:
    crash_files = [p for p in crash_dir.iterdir() if p.is_file() and not p.name.startswith("README")]
    crash_files = sorted(crash_files)[:limit]

    if not crash_files:
        return "No crash files found."

    chunks: list[str] = []
    for path in crash_files:
        data = path.read_bytes()
        chunks.append(
            f"## {path.name}\n"
            f"size={len(data)} bytes\n"
            f"hex={data[:128].hex()}\n"
        )
    return "\n".join(chunks)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate LLM-assisted AFL++ crash triage report")
    parser.add_argument("--target", required=True)
    parser.add_argument("--crashes", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--model", default=os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:7b"))
    parser.add_argument("--base-url", default=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"))
    args = parser.parse_args()

    crash_dir = Path(args.crashes)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    crash_summary = read_crash_files(crash_dir, args.limit)
    user_prompt = f"""
Target: {args.target}

Crash artifacts:
{crash_summary}

Create a concise Markdown crash triage report with these sections:
1. Summary
2. Reproduction command placeholder
3. Input characteristics
4. Likely root cause hypothesis
5. Security impact
6. Recommended fixes
7. Next experiments
""".strip()

    client = OllamaClient(model=args.model, base_url=args.base_url)
    report = client.chat(SYSTEM_PROMPT, user_prompt)
    out_path.write_text(report + "\n", encoding="utf-8")
    print(f"Wrote crash report to {out_path}")


if __name__ == "__main__":
    main()
