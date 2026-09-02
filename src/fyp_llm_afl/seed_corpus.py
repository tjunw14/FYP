from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path


def prepare_corpus(input_dirs: list[Path], out_dir: Path, clean: bool, max_bytes: int) -> dict[str, int]:
    out_dir.mkdir(parents=True, exist_ok=True)

    if clean:
        for existing in out_dir.glob("*.bin"):
            existing.unlink()

    candidates: list[Path] = []
    for input_dir in input_dirs:
        if not input_dir.is_dir():
            raise SystemExit(f"Seed directory does not exist: {input_dir}")
        candidates.extend(sorted(input_dir.glob("*.bin")))

    if not candidates:
        raise SystemExit("No .bin seed files were found in the supplied input directories.")

    seen_hashes: set[str] = set()
    accepted: list[tuple[Path, bytes, str]] = []
    rejected_empty = 0
    rejected_large = 0
    duplicates = 0

    for source in candidates:
        data = source.read_bytes()
        if not data:
            rejected_empty += 1
            continue
        if len(data) > max_bytes:
            rejected_large += 1
            continue

        digest = hashlib.sha256(data).hexdigest()
        if digest in seen_hashes:
            duplicates += 1
            continue

        seen_hashes.add(digest)
        accepted.append((source, data, digest))

    if not accepted:
        raise SystemExit("No valid seed files remained after validation and de-duplication.")

    manifest_path = out_dir / "manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["filename", "source_path", "size_bytes", "sha256", "hex"])

        for index, (source, data, digest) in enumerate(accepted, start=1):
            filename = f"seed_{index:03d}.bin"
            destination = out_dir / filename
            shutil.copyfile(source, destination)
            writer.writerow([filename, source.as_posix(), len(data), digest, data.hex()])

    summary = {
        "candidate_files": len(candidates),
        "accepted_unique_seeds": len(accepted),
        "duplicate_seeds_removed": duplicates,
        "empty_seeds_rejected": rejected_empty,
        "oversized_seeds_rejected": rejected_large,
        "max_seed_bytes": max_bytes,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a clean, binary-only AFL++ input corpus from one or more seed directories."
    )
    parser.add_argument(
        "--input",
        action="append",
        required=True,
        type=Path,
        help="Directory containing .bin seed files. Repeat --input to merge multiple sources.",
    )
    parser.add_argument("--out", required=True, type=Path, help="Output directory for the clean corpus.")
    parser.add_argument("--clean", action="store_true", help="Delete existing .bin files in the output directory first.")
    parser.add_argument(
        "--max-bytes",
        default=4096,
        type=int,
        help="Reject individual seeds larger than this size. Default: 4096 bytes.",
    )
    args = parser.parse_args()

    if args.max_bytes < 1:
        raise SystemExit("--max-bytes must be at least 1")

    summary = prepare_corpus(args.input, args.out, args.clean, args.max_bytes)
    print(f"Prepared {summary['accepted_unique_seeds']} unique seed(s) in {args.out}")
    print(f"Removed {summary['duplicate_seeds_removed']} duplicate seed(s)")
    print(f"Manifest: {args.out / 'manifest.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
