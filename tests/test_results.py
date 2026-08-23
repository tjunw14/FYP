from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from fyp_llm_afl.results import collect_results


class ResultCollectorTests(unittest.TestCase):
    def test_collect_results_writes_expected_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            afl_instance = root / "out" / "default"
            report_dir = root / "report"
            (afl_instance / "crashes").mkdir(parents=True)
            (afl_instance / "hangs").mkdir(parents=True)

            (afl_instance / "fuzzer_stats").write_text(
                "afl_version        : ++5.02a\n"
                "run_time           : 900\n"
                "execs_done         : 12345\n"
                "execs_per_sec      : 13.72\n"
                "corpus_count       : 100\n"
                "bitmap_cvg         : 3.00%\n"
                "saved_crashes      : 1\n"
                "saved_hangs        : 0\n"
                "stability          : 100.00%\n"
                "command_line       : afl-fuzz -i seeds -o out -- ./target @@\n",
                encoding="utf-8",
            )
            (afl_instance / "crashes" / "README.txt").write_text("metadata", encoding="utf-8")
            (afl_instance / "crashes" / "id:000000").write_bytes(b"crash")
            (afl_instance / "hangs" / "README.txt").write_text("metadata", encoding="utf-8")

            summary = collect_results(afl_instance, report_dir)

            self.assertEqual(summary["afl_version"], "++5.02a")
            self.assertEqual(summary["crash_files_counted"], 1)
            self.assertEqual(summary["hang_files_counted"], 0)
            self.assertEqual((report_dir / "crash_count.txt").read_text().strip(), "1")
            self.assertEqual((report_dir / "hang_count.txt").read_text().strip(), "0")
            self.assertTrue((report_dir / "fuzzer_stats.txt").is_file())
            self.assertTrue((report_dir / "summary.md").is_file())

            saved_summary = json.loads((report_dir / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(saved_summary["execs_done"], "12345")


if __name__ == "__main__":
    unittest.main()
