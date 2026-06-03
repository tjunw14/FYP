from __future__ import annotations

import argparse
import os
from pathlib import Path

from .ollama_client import OllamaClient


SYSTEM_PROMPT = """You are assisting with defensive vulnerability analysis for a university FYP.
Be conservative and evidence-based.
Do not claim buffer overflow, integer overflow, arbitrary code execution, or exploitable vulnerability unless the provided evidence directly supports it.
Do not provide exploit-building instructions.
Focus on crash behaviour, likely parser path, reproducibility, limitations, and defensive fixes.
Return Markdown, not JSON.
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
            f"hex_prefix={data[:128].hex()}\n"
        )
    return "\n".join(chunks)


def toy_target_context() -> str:
    return """
Important context for toy_nas_tlv:
- This is an educational NAS-like TLV parser used to validate the AFL++ pipeline.
- The target intentionally calls abort() when message_type == 0x41, payload_len >= 4, and parser score > 10.
- Therefore crashes with SIGABRT/signal 6 are expected validation crashes, not proven memory-corruption vulnerabilities.
- The correct interpretation is that AFL++ discovered inputs that reach the intentional crash condition.
""".strip()


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
    target_context = toy_target_context() if args.target == "toy_nas_tlv" else "No special target context provided."

    user_prompt = f"""
Target: {args.target}

Target context:
{target_context}

Crash artifacts:
{crash_summary}

Create a concise Markdown crash triage report with these sections:
1. Summary
2. What AFL++ found
3. Reproduction command placeholder
4. Input characteristics
5. Likely root cause hypothesis
6. Security impact and limitations
7. Recommended defensive fixes
8. Next experiments

Important constraints:
- Be clear when a conclusion is only a hypothesis.
- For toy_nas_tlv, state that signal 6/SIGABRT is expected because the program intentionally calls abort().
- Do not describe exploit construction.
""".strip()

    client = OllamaClient(model=args.model, base_url=args.base_url)
    report = client.chat(SYSTEM_PROMPT, user_prompt, json_mode=False)
    out_path.write_text(report + "\n", encoding="utf-8")
    print(f"Wrote crash report to {out_path}")


if __name__ == "__main__":
    main()
