from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def parse_fuzzer_stats(path: Path) -> dict[str, str]:
    stats: dict[str, str] = {}
    for raw_line in path.read_text(errors="replace").splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        stats[key.strip()] = value.strip()
    return stats


def count_artifacts(directory: Path) -> int:
    if not directory.is_dir():
        return 0
    return sum(1 for path in directory.iterdir() if path.is_file() and path.name != "README.txt")


def build_markdown(stats: dict[str, str], crash_files: int, hang_files: int) -> str:
    fields = [
        ("AFL++ version", "afl_version"),
        ("Runtime (s)", "run_time"),
        ("Executions", "execs_done"),
        ("Executions/sec", "execs_per_sec"),
        ("Corpus count", "corpus_count"),
        ("Corpus found", "corpus_found"),
        ("Corpus favored", "corpus_favored"),
        ("Max depth", "max_depth"),
        ("Bitmap coverage", "bitmap_cvg"),
        ("Edges found", "edges_found"),
        ("Total edges", "total_edges"),
        ("Saved crashes (AFL++)", "saved_crashes"),
        ("Saved hangs (AFL++)", "saved_hangs"),
        ("Total timeouts", "total_tmouts"),
        ("Stability", "stability"),
    ]

    rows = ["| Metric | Value |", "|---|---:|"]
    for label, key in fields:
        rows.append(f"| {label} | {stats.get(key, 'Not recorded')} |")
    rows.append(f"| Crash files counted | {crash_files} |")
    rows.append(f"| Hang files counted | {hang_files} |")

    command = stats.get("command_line", "Not recorded")
    conclusion = (
        "This file records observed AFL++ evidence only. A saved crash is not automatically a confirmed vulnerability, "
        "and a no-crash run does not prove that the target is secure."
    )

    return "\n".join(
        [
            "# AFL++ Experiment Evidence Summary",
            "",
            *rows,
            "",
            "## AFL++ command line",
            "",
            f"`{command}`",
            "",
            "## Interpretation boundary",
            "",
            conclusion,
            "",
        ]
    )


def collect_results(afl_instance: Path, report_dir: Path) -> dict[str, object]:
    stats_path = afl_instance / "fuzzer_stats"
    if not stats_path.is_file():
        raise SystemExit(f"AFL++ fuzzer_stats not found: {stats_path}")

    stats = parse_fuzzer_stats(stats_path)
    crash_files = count_artifacts(afl_instance / "crashes")
    hang_files = count_artifacts(afl_instance / "hangs")

    report_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(stats_path, report_dir / "fuzzer_stats.txt")
    (report_dir / "crash_count.txt").write_text(f"{crash_files}\n", encoding="utf-8")
    (report_dir / "hang_count.txt").write_text(f"{hang_files}\n", encoding="utf-8")

    summary: dict[str, object] = {
        "afl_instance": str(afl_instance),
        "afl_version": stats.get("afl_version"),
        "run_time": stats.get("run_time"),
        "execs_done": stats.get("execs_done"),
        "execs_per_sec": stats.get("execs_per_sec"),
        "corpus_count": stats.get("corpus_count"),
        "corpus_found": stats.get("corpus_found"),
        "corpus_favored": stats.get("corpus_favored"),
        "max_depth": stats.get("max_depth"),
        "bitmap_cvg": stats.get("bitmap_cvg"),
        "edges_found": stats.get("edges_found"),
        "total_edges": stats.get("total_edges"),
        "saved_crashes": stats.get("saved_crashes"),
        "saved_hangs": stats.get("saved_hangs"),
        "total_tmouts": stats.get("total_tmouts"),
        "stability": stats.get("stability"),
        "crash_files_counted": crash_files,
        "hang_files_counted": hang_files,
        "command_line": stats.get("command_line"),
    }

    (report_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (report_dir / "summary.md").write_text(build_markdown(stats, crash_files, hang_files), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect factual AFL++ experiment evidence into report files.")
    parser.add_argument(
        "--afl-instance",
        required=True,
        type=Path,
        help="AFL++ instance directory containing fuzzer_stats, crashes/, and hangs/ (usually <out>/default).",
    )
    parser.add_argument("--report-dir", required=True, type=Path, help="Destination directory for evidence files.")
    args = parser.parse_args()

    summary = collect_results(args.afl_instance, args.report_dir)
    print(f"Evidence written to {args.report_dir}")
    print(f"Crash files: {summary['crash_files_counted']}; hang files: {summary['hang_files_counted']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
