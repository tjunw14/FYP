from __future__ import annotations

import json
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from fyp_llm_afl.results import count_artifacts, parse_fuzzer_stats


@dataclass
class FuzzSession:
    container_name: str
    output_dir: Path
    report_dir: Path
    duration_seconds: int
    dictionary_enabled: bool
    started_at: float = field(default_factory=time.time)
    process: subprocess.Popen[str] | None = None
    return_code: int | None = None
    stopped_by_user: bool = False
    log_lines: list[str] = field(default_factory=list)


class FuzzManager:
    """Own one local Open5GS fuzzing session at a time.

    The browser never supplies a shell command. The manager constructs a fixed Docker
    invocation for the repository's Open5GS harness and seed corpus only.
    """

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()
        self._lock = threading.Lock()
        self._session: FuzzSession | None = None

    @property
    def session(self) -> FuzzSession | None:
        with self._lock:
            return self._session

    def _append_log(self, session: FuzzSession, line: str) -> None:
        with self._lock:
            session.log_lines.append(line.rstrip())
            if len(session.log_lines) > 300:
                del session.log_lines[:-300]

    def _watch_process(self, session: FuzzSession) -> None:
        assert session.process is not None
        process = session.process
        if process.stdout is not None:
            for line in process.stdout:
                self._append_log(session, line)
        code = process.wait()
        with self._lock:
            session.return_code = code

    def start(self, duration_seconds: int = 900, dictionary_enabled: bool = False) -> dict[str, object]:
        if duration_seconds < 30 or duration_seconds > 86400:
            raise ValueError("duration_seconds must be between 30 and 86400")

        with self._lock:
            if self._session and self._session.process and self._session.process.poll() is None:
                raise RuntimeError("A fuzzing session is already running")

        clean_seed_dir = self.repo_root / "targets/open5gs/seeds_registration_webllm_clean"
        if not any(clean_seed_dir.glob("*.bin")):
            raise RuntimeError("No validated WebLLM seed corpus exists. Validate seeds first.")

        open5gs_build = self.repo_root / "external/open5gs/build/lib/nas/5gs/libogsnas-5gs.so"
        if not open5gs_build.is_file():
            raise RuntimeError(
                "Open5GS build artifacts were not found under external/open5gs/build. "
                "Restore/build Open5GS before starting fuzzing."
            )

        stamp = time.strftime("%Y%m%d_%H%M%S")
        container_name = f"fyp-open5gs-{stamp}"
        output_dir = self.repo_root / "targets/open5gs/out_registration_webllm_ui"
        report_dir = self.repo_root / "reports/open5gs/webllm_ui_run"
        dictionary = "targets/open5gs/nas_registration_request.dict" if dictionary_enabled else "-"
        duration = f"{duration_seconds}s"

        # One container builds the local harness and runs AFL++. The repository is
        # mounted at /work so fuzzer_stats is visible to the host while AFL++ runs.
        container_script = " && ".join(
            [
                "apt-get update -qq",
                "DEBIAN_FRONTEND=noninteractive apt-get install -y -qq libtalloc-dev pkg-config >/tmp/fyp-apt.log",
                "bash /work/scripts/build_open5gs_harness.sh",
                (
                    "bash /work/scripts/run_open5gs_fuzz.sh "
                    "targets/open5gs/seeds_registration_webllm_clean "
                    "targets/open5gs/out_registration_webllm_ui "
                    f"{duration} "
                    "reports/open5gs/webllm_ui_run "
                    f"{dictionary}"
                ),
            ]
        )

        command = [
            "docker",
            "run",
            "--rm",
            "--name",
            container_name,
            "-v",
            f"{self.repo_root}:/work",
            "aflplusplus/aflplusplus",
            "bash",
            "-lc",
            container_script,
        ]

        process = subprocess.Popen(
            command,
            cwd=self.repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        session = FuzzSession(
            container_name=container_name,
            output_dir=output_dir,
            report_dir=report_dir,
            duration_seconds=duration_seconds,
            dictionary_enabled=dictionary_enabled,
            process=process,
        )
        with self._lock:
            self._session = session

        threading.Thread(target=self._watch_process, args=(session,), daemon=True).start()
        return self.status()

    def stop(self) -> dict[str, object]:
        session = self.session
        if not session or not session.process or session.process.poll() is not None:
            return self.status()

        session.stopped_by_user = True
        subprocess.run(
            ["docker", "stop", "--time", "2", session.container_name],
            cwd=self.repo_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return self.status()

    def _stats(self, session: FuzzSession) -> dict[str, str]:
        stats_path = session.output_dir / "default/fuzzer_stats"
        if not stats_path.is_file():
            return {}
        try:
            return parse_fuzzer_stats(stats_path)
        except OSError:
            return {}

    def status(self) -> dict[str, object]:
        session = self.session
        if not session:
            return {"state": "idle", "running": False, "stats": {}, "log_tail": []}

        process = session.process
        running = bool(process and process.poll() is None)
        stats = self._stats(session)
        elapsed = max(0, int(time.time() - session.started_at))

        if running:
            state = "running"
        elif session.stopped_by_user:
            state = "stopped"
        elif session.return_code == 0:
            state = "completed"
        elif session.return_code is None:
            state = "starting"
        else:
            state = "failed"

        crash_dir = session.output_dir / "default/crashes"
        hang_dir = session.output_dir / "default/hangs"
        return {
            "state": state,
            "running": running,
            "elapsed_seconds": elapsed,
            "requested_duration_seconds": session.duration_seconds,
            "dictionary_enabled": session.dictionary_enabled,
            "return_code": session.return_code,
            "stats": stats,
            "crash_files": count_artifacts(crash_dir),
            "hang_files": count_artifacts(hang_dir),
            "report_dir": str(session.report_dir.relative_to(self.repo_root)),
            "log_tail": list(session.log_lines[-40:]),
        }

    def evidence(self) -> dict[str, object]:
        status = self.status()
        session = self.session
        if not session:
            return status

        summary_path = session.report_dir / "summary.json"
        if summary_path.is_file():
            try:
                status["summary"] = json.loads(summary_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                pass
        return status
