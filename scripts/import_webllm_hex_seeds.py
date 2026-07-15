#!/usr/bin/env python3
"""Import WebLLM-generated hexadecimal AFL++ seeds.

The WebLLM browser demo may produce clean seed lines such as:

    seed_001: 4101f0
    seed_002: 7e0041012e00

Small browser LLMs may also output comma-separated byte lists such as:

    seed_001: 4a, 52, 53, 2e, 2f, 40

This script accepts both styles. If WebLLM produces a very long byte sequence, the
sequence is split into multiple small AFL++ seed files.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

LABELLED_BLOCK_RE = re.compile(
    r"\bseed[_-]?\d{1,3}\b\s*[:=]\s*([\s\S]*?)(?=\bseed[_-]?\d{1,3}\b\s*[:=]|$)",
    re.IGNORECASE,
)
HEX_TOKEN_RE = re.compile(r"0x[0-9a-fA-F]{2}|\b[0-9a-fA-F]{2}\b|\b[0-9a-fA-F]{8,128}\b")


def extract_bytes(segment: str) -> list[str]:
    """Extract byte-sized hex tokens from a text segment.

    Supports both compact hex strings and comma/space-separated byte values.
    """
    out: list[str] = []

    for token in HEX_TOKEN_RE.findall(segment):
        cleaned = re.sub(r"^0x", "", token, flags=re.IGNORECASE).lower()
        if not re.fullmatch(r"[0-9a-f]+", cleaned):
            continue
        if len(cleaned) % 2 != 0:
            continue

        for idx in range(0, len(cleaned), 2):
            out.append(cleaned[idx : idx + 2])

    return out


def append_seed_chunks(seeds: list[tuple[str, bytes, str]], bytes_hex: list[str], max_seeds: int, chunk_size: int) -> None:
    """Append byte chunks as sequential AFL++ seed entries."""
    if len(bytes_hex) < 2:
        return

    for idx in range(0, len(bytes_hex), chunk_size):
        if len(seeds) >= max_seeds:
            return

        chunk = bytes_hex[idx : idx + chunk_size]
        if len(chunk) < 2:
            continue

        hex_text = "".join(chunk)
        name = f"seed_{len(seeds) + 1:03d}"
        try:
            data = bytes.fromhex(hex_text)
        except ValueError:
            continue
        seeds.append((name, data, hex_text))


def parse_seed_lines(text: str, max_seeds: int = 20, chunk_size: int = 16) -> list[tuple[str, bytes, str]]:
    """Parse WebLLM output into seed entries.

    The function first looks for labelled seed blocks. If no labelled seed blocks
    are found, it falls back to extracting all hex-looking bytes from the text.
    """
    seeds: list[tuple[str, bytes, str]] = []

    labelled_blocks = list(LABELLED_BLOCK_RE.finditer(text))
    if labelled_blocks:
        for match in labelled_blocks:
            if len(seeds) >= max_seeds:
                break
            append_seed_chunks(seeds, extract_bytes(match.group(1)), max_seeds=max_seeds, chunk_size=chunk_size)
    else:
        append_seed_chunks(seeds, extract_bytes(text), max_seeds=max_seeds, chunk_size=chunk_size)

    return seeds


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert WebLLM-generated hex seed lines into AFL++ binary seed files.")
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Text file containing WebLLM seed lines, for example webllm_demo/webllm_generated_seeds.txt",
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
    parser.add_argument(
        "--max-seeds",
        default=20,
        type=int,
        help="Maximum number of seed files to write.",
    )
    parser.add_argument(
        "--chunk-size",
        default=16,
        type=int,
        help="Number of bytes per generated seed chunk when splitting long WebLLM output.",
    )
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input file does not exist: {args.input}")

    text = args.input.read_text(encoding="utf-8")
    seeds = parse_seed_lines(text, max_seeds=args.max_seeds, chunk_size=args.chunk_size)

    if not seeds:
        raise SystemExit("No valid seed bytes were found. Check the WebLLM output format.")

    args.output.mkdir(parents=True, exist_ok=True)

    if args.clean:
        for existing in args.output.glob("*.bin"):
            existing.unlink()

    for index, (name, data, hex_text) in enumerate(seeds, start=1):
        filename = f"{index:03d}_{name}.bin"
        output_path = args.output / filename
        output_path.write_bytes(data)
        print(f"[write] {output_path} ({len(data)} bytes)")

    manifest_path = args.output / "manifest.csv"
    manifest_lines = ["filename,size_bytes,hex"]
    for index, (name, data, hex_text) in enumerate(seeds, start=1):
        filename = f"{index:03d}_{name}.bin"
        manifest_lines.append(f"{filename},{len(data)},{hex_text}")
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

    print(f"[write] {manifest_path}")
    print(f"Imported {len(seeds)} seed(s) into {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
