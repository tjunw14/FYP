#!/usr/bin/env python3
"""Import WebLLM-generated hexadecimal AFL++ seeds.

The WebLLM browser demo produces seed lines such as:

    seed_001: 4101f0
    seed_002: 7e0041012e00

This script parses those lines and writes one binary .bin file per seed into the
Open5GS WebLLM seed directory.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

SEED_RE = re.compile(r"\b(seed[_-]?\d{1,3})\b\s*[:=]\s*([0-9a-fA-F\s]+)")


def normalise_seed_name(raw_name: str) -> str:
    return raw_name.replace("-", "_").lower()


def parse_seed_lines(text: str) -> list[tuple[str, bytes, str]]:
    seeds: list[tuple[str, bytes, str]] = []
    seen: set[str] = set()

    for line_no, line in enumerate(text.splitlines(), start=1):
        match = SEED_RE.search(line)
        if not match:
            continue

        name = normalise_seed_name(match.group(1))
        hex_text = re.sub(r"\s+", "", match.group(2)).lower()

        if name in seen:
            print(f"[skip] duplicate seed name on line {line_no}: {name}")
            continue
        if not hex_text:
            print(f"[skip] empty hex on line {line_no}: {name}")
            continue
        if len(hex_text) % 2 != 0:
            print(f"[skip] odd-length hex on line {line_no}: {name} -> {hex_text}")
            continue
        if not re.fullmatch(r"[0-9a-f]+", hex_text):
            print(f"[skip] non-hex characters on line {line_no}: {name} -> {hex_text}")
            continue
        if len(hex_text) > 128:
            print(f"[skip] seed is longer than 64 bytes on line {line_no}: {name}")
            continue

        try:
            data = bytes.fromhex(hex_text)
        except ValueError as exc:
            print(f"[skip] invalid hex on line {line_no}: {name} -> {exc}")
            continue

        seen.add(name)
        seeds.append((name, data, hex_text))

    return seeds


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert WebLLM-generated hex seed lines into AFL++ binary seed files.")
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Text file containing WebLLM seed lines, for example reports/open5gs/phase5_webllm_demo/webllm_generated_seeds.txt",
    )
    parser.add_argument(
        "--output",
        default=Path("targets/open5gs/seeds_registration_webllm"),
        type=Path,
        help="Output directory for binary seed files.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete existing .bin files in the output directory before writing new seeds.",
    )
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input file does not exist: {args.input}")

    text = args.input.read_text(encoding="utf-8")
    seeds = parse_seed_lines(text)

    if not seeds:
        raise SystemExit("No valid seed lines were found. Check the WebLLM output format.")

    args.output.mkdir(parents=True, exist_ok=True)

    if args.clean:
        for existing in args.output.glob("*.bin"):
            existing.unlink()

    manifest_lines = ["# WebLLM-generated Open5GS AFL++ seeds", ""]

    for index, (name, data, hex_text) in enumerate(seeds, start=1):
        filename = f"{index:03d}_{name}.bin"
        output_path = args.output / filename
        output_path.write_bytes(data)
        manifest_lines.append(f"{filename},{len(data)},{hex_text}")
        print(f"[write] {output_path} ({len(data)} bytes)")

    manifest_path = args.output / "manifest.csv"
    manifest_path.write_text("filename,size_bytes,hex\n" + "\n".join(manifest_lines[2:]) + "\n", encoding="utf-8")
    print(f"[write] {manifest_path}")
    print(f"Imported {len(seeds)} seed(s) into {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
