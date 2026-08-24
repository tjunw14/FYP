from __future__ import annotations

import argparse
import json
import re
import shutil
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from fyp_llm_afl.api.fuzz_manager import FuzzManager
from fyp_llm_afl.seed_corpus import prepare_corpus


SEED_LINE_RE = re.compile(r"^seed[_-]?(\d{1,3})\s*:\s*([0-9a-fA-F]{4,8192})\s*$", re.IGNORECASE)
MAX_REQUEST_BYTES = 1024 * 1024


def parse_seed_text(text: str) -> list[tuple[str, bytes, str]]:
    seeds: list[tuple[str, bytes, str]] = []
    seen: set[bytes] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = SEED_LINE_RE.fullmatch(line)
        if not match:
            raise ValueError(f"Invalid seed line: {line[:120]}")
        hex_text = match.group(2).lower()
        if len(hex_text) % 2:
            raise ValueError(f"Seed has an odd number of hex characters: {line[:120]}")
        data = bytes.fromhex(hex_text)
        if not 2 <= len(data) <= 4096:
            raise ValueError("Each seed must contain between 2 and 4096 bytes")
        if data in seen:
            continue
        seen.add(data)
        seeds.append((f"seed_{len(seeds) + 1:03d}", data, hex_text))
    if not seeds:
        raise ValueError("No valid seed lines were supplied")
    if len(seeds) > 100:
        raise ValueError("At most 100 seed lines may be validated at once")
    return seeds


def write_webllm_seeds(repo_root: Path, text: str) -> dict[str, Any]:
    seeds = parse_seed_text(text)
    source_dir = repo_root / "targets/open5gs/seeds_registration_webllm"
    clean_dir = repo_root / "targets/open5gs/seeds_registration_webllm_clean"
    source_dir.mkdir(parents=True, exist_ok=True)

    for existing in source_dir.glob("*.bin"):
        existing.unlink()

    manifest_lines = ["filename,size_bytes,hex"]
    preview: list[dict[str, Any]] = []
    for index, (name, data, hex_text) in enumerate(seeds, start=1):
        filename = f"{index:03d}_{name}.bin"
        (source_dir / filename).write_bytes(data)
        manifest_lines.append(f"{filename},{len(data)},{hex_text}")
        preview.append({"filename": filename, "size_bytes": len(data), "hex": hex_text})

    (source_dir / "manifest.csv").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    (repo_root / "webllm_demo/webllm_generated_seeds.txt").write_text(text.strip() + "\n", encoding="utf-8")

    corpus_summary = prepare_corpus([source_dir], clean_dir, clean=True, max_bytes=4096)
    return {
        "validated": True,
        "input_seed_count": len(seeds),
        "clean_seed_count": corpus_summary["accepted_unique_seeds"],
        "preview": preview,
        "clean_corpus": "targets/open5gs/seeds_registration_webllm_clean",
        "corpus_summary": corpus_summary,
    }


def load_targets(repo_root: Path) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for path in sorted((repo_root / "configs").glob("*.json")):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if item.get("target_id") and item.get("decoder_function"):
            targets.append(item)
    return targets


def build_triage_prompt(evidence: dict[str, Any]) -> str:
    stats = evidence.get("stats") or evidence.get("summary") or {}
    crash_count = evidence.get("crash_files", 0)
    hang_count = evidence.get("hang_files", 0)
    return f"""You are assisting with defensive fuzzing-result triage for an Open5GS NAS parser.

Use only the evidence below. Do not infer a vulnerability merely because fuzzing was performed. A saved crash is not automatically a vulnerability, and a run with zero crashes does not prove the target is secure. Clearly separate observed facts from possible follow-up investigation. Do not provide exploitation instructions.

Target: Open5GS NAS 5GS Registration Request decoder
Function: ogs_nas_5gs_decode_registration_request()

Observed AFL++ evidence:
{json.dumps(stats, indent=2)}

Counted crash files: {crash_count}
Counted hang files: {hang_count}
Session state: {evidence.get('state', 'unknown')}

Produce the following sections:
1. Evidence Summary
2. Conservative Assessment
3. Crash/Hang Interpretation
4. Recommended Defensive Follow-up
5. Final Conclusion

If crash and hang counts are zero, explicitly state that no crash or hang was observed in this recorded run and that no vulnerability claim is supported by this evidence.
"""


def export_report(repo_root: Path, evidence: dict[str, Any], analysis: str, seed_info: dict[str, Any] | None) -> tuple[Path, str]:
    report_dir = repo_root / "reports/open5gs/webllm_ui_run"
    report_dir.mkdir(parents=True, exist_ok=True)
    stats = evidence.get("stats") or evidence.get("summary") or {}
    lines = [
        "# WebLLM-Driven Open5GS Fuzzing Report",
        "",
        "## Workflow",
        "",
        "WebLLM generated candidate Open5GS NAS seed inputs in the browser. The local backend validated and converted the seeds into a binary-only AFL++ corpus, launched the existing instrumented Open5GS harness in Docker, collected AFL++ evidence, and returned that factual evidence to WebLLM for guarded analysis.",
        "",
        "## Seed Validation",
        "",
        f"Validated seed count: {(seed_info or {}).get('clean_seed_count', 'Not recorded')}",
        "",
        "## AFL++ Evidence",
        "",
        "```json",
        json.dumps(stats, indent=2),
        "```",
        "",
        f"Crash files counted: {evidence.get('crash_files', 0)}",
        "",
        f"Hang files counted: {evidence.get('hang_files', 0)}",
        "",
        "## WebLLM Guarded Analysis",
        "",
        analysis.strip() or "No WebLLM analysis was supplied.",
        "",
        "## Interpretation Boundary",
        "",
        "A saved AFL++ crash is not automatically a confirmed vulnerability. Conversely, a no-crash run does not prove that Open5GS is secure. Final security conclusions require reproducible evidence, source-code review, sanitizer evidence where applicable, and human verification.",
        "",
    ]
    markdown = "\n".join(lines)
    path = report_dir / "exported_webllm_fuzzing_report.md"
    path.write_text(markdown, encoding="utf-8")
    return path, markdown


class WorkbenchHandler(SimpleHTTPRequestHandler):
    repo_root: Path
    fuzz_manager: FuzzManager
    last_seed_info: dict[str, Any] | None = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(self.repo_root), **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[web] {self.address_string()} - {format % args}")

    def _json(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length < 0 or length > MAX_REQUEST_BYTES:
            raise ValueError("Request body is too large")
        data = self.rfile.read(length) if length else b"{}"
        parsed = json.loads(data.decode("utf-8"))
        if not isinstance(parsed, dict):
            raise ValueError("JSON body must be an object")
        return parsed

    def do_GET(self) -> None:
        if self.path == "/":
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", "/webllm_demo/")
            self.end_headers()
            return
        if self.path == "/api/health":
            self._json({"ok": True, "service": "fyp-local-workbench"})
            return
        if self.path == "/api/targets":
            self._json({"targets": load_targets(self.repo_root)})
            return
        if self.path == "/api/fuzz/status":
            self._json(self.fuzz_manager.status())
            return
        if self.path == "/api/fuzz/results":
            self._json(self.fuzz_manager.evidence())
            return
        if self.path == "/api/triage/evidence":
            evidence = self.fuzz_manager.evidence()
            self._json({"evidence": evidence, "prompt": build_triage_prompt(evidence)})
            return
        super().do_GET()

    def do_POST(self) -> None:
        try:
            body = self._body_json()
            if self.path == "/api/seeds/validate":
                seed_text = str(body.get("seed_text", ""))
                info = write_webllm_seeds(self.repo_root, seed_text)
                type(self).last_seed_info = info
                self._json(info)
                return

            if self.path == "/api/fuzz/start":
                target_id = str(body.get("target_id", "open5gs_registration_request"))
                if target_id != "open5gs_registration_request":
                    raise ValueError("Only the configured Open5GS Registration Request target is enabled")
                duration_seconds = int(body.get("duration_seconds", 900))
                dictionary_enabled = bool(body.get("dictionary_enabled", False))
                self._json(self.fuzz_manager.start(duration_seconds, dictionary_enabled), status=HTTPStatus.ACCEPTED)
                return

            if self.path == "/api/fuzz/stop":
                self._json(self.fuzz_manager.stop())
                return

            if self.path == "/api/report/export":
                analysis = str(body.get("analysis", ""))
                evidence = self.fuzz_manager.evidence()
                path, markdown = export_report(self.repo_root, evidence, analysis, type(self).last_seed_info)
                self._json({"saved": True, "path": str(path.relative_to(self.repo_root)), "markdown": markdown})
                return

            self._json({"error": "Unknown API endpoint"}, status=HTTPStatus.NOT_FOUND)
        except (ValueError, json.JSONDecodeError) as exc:
            self._json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except (RuntimeError, FileNotFoundError) as exc:
            self._json({"error": str(exc)}, status=HTTPStatus.CONFLICT)
        except Exception as exc:  # Local demo: return concise failure to UI and keep server alive.
            self._json({"error": f"Backend error: {exc}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local FYP WebLLM/AFL++ workbench server.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address. Default: 127.0.0.1")
    parser.add_argument("--port", type=int, default=8000, help="Port. Default: 8000")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[3]
    WorkbenchHandler.repo_root = repo_root
    WorkbenchHandler.fuzz_manager = FuzzManager(repo_root)

    server = ThreadingHTTPServer((args.host, args.port), WorkbenchHandler)
    print(f"FYP workbench: http://{args.host}:{args.port}/webllm_demo/")
    print("Press Ctrl+C to stop the local server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
