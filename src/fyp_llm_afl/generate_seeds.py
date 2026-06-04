from __future__ import annotations

import argparse
import os
from pathlib import Path

from .ollama_client import OllamaClient, extract_json_array


SYSTEM_PROMPT = """You help with defensive software testing.
Generate fuzzing seed inputs for AFL++.
Return only a JSON array of hex strings. Do not include prose.
The seeds are for defensive fuzz testing only.
"""


def build_prompt(target: str, count: int) -> str:
    if target == "toy_nas_tlv":
        return f"""
The target is a toy NAS-like TLV parser used for an AFL++ smoke test.
Input format:
- byte 0: message_type
- byte 1: payload_length
- remaining bytes: TLV fields
- each TLV field: tag, length, value bytes

Generate {count} diverse binary seed inputs as hex strings.
Include valid, near-valid, boundary, empty-ish, nested-looking, and malformed-length examples.
Return only JSON, for example: ["0100", "0103010100"].
""".strip()

    if target in {"open5gs_registration", "open5gs_nas_registration"}:
        return f"""
The target is an AFL++ harness for Open5GS NAS 5GS Registration Request decoding.
The harness calls:
  ogs_nas_5gs_decode_registration_request(message, pkbuf)

Important input interpretation:
- The AFL++ input is treated as the body of a NAS 5GS Registration Request.
- The NAS message type/security header has already been consumed by the harness design.
- The decoder first expects a 5GS registration type field.
- It then expects a 5GS mobile identity field.
- Remaining bytes are interpreted as optional Information Elements.

Generate {count} diverse seed inputs as hex strings.
Seeds should be useful for parser exploration, not exploitation.
Include:
- very short malformed examples
- near-valid registration request bodies
- examples with small mobile identity lengths
- examples with optional IE-like trailing bytes
- boundary examples with inconsistent or oversized length fields
- varied first byte values to exercise registration type decoding

Return only JSON, for example:
["010001", "79020102", "01050102030405", "010201027900"]
""".strip()

    return f"Generate {count} diverse hex-encoded fuzzing seeds for target {target}."


def write_seed(hex_string: str, path: Path) -> None:
    cleaned = "".join(hex_string.split()).lower().replace("0x", "")
    if len(cleaned) % 2 != 0:
        cleaned = "0" + cleaned
    path.write_bytes(bytes.fromhex(cleaned))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate LLM-assisted AFL++ seed inputs")
    parser.add_argument("--target", default="toy_nas_tlv")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--out", required=True)
    parser.add_argument("--model", default=os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:7b"))
    parser.add_argument("--base-url", default=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"))
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    client = OllamaClient(model=args.model, base_url=args.base_url)
    response = client.chat(SYSTEM_PROMPT, build_prompt(args.target, args.count), json_mode=True)
    seeds = extract_json_array(response)

    for index, seed in enumerate(seeds[: args.count], start=1):
        write_seed(str(seed), out_dir / f"seed_{index:03d}.bin")

    print(f"Wrote {min(len(seeds), args.count)} seeds to {out_dir}")


if __name__ == "__main__":
    main()
