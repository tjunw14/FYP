from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from fyp_llm_afl.seed_corpus import prepare_corpus


class SeedCorpusTests(unittest.TestCase):
    def test_prepare_corpus_filters_non_binary_and_deduplicates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_a = root / "a"
            source_b = root / "b"
            output = root / "out"
            source_a.mkdir()
            source_b.mkdir()

            (source_a / "one.bin").write_bytes(b"\x01\x02")
            (source_a / "duplicate.bin").write_bytes(b"\x01\x02")
            (source_b / "two.bin").write_bytes(b"\x03\x04\x05")
            (source_b / "README.md").write_text("not an AFL seed", encoding="utf-8")

            summary = prepare_corpus([source_a, source_b], output, clean=True, max_bytes=32)

            self.assertEqual(summary["candidate_files"], 3)
            self.assertEqual(summary["accepted_unique_seeds"], 2)
            self.assertEqual(summary["duplicate_seeds_removed"], 1)
            self.assertEqual(len(list(output.glob("*.bin"))), 2)

            with (output / "manifest.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 2)
            self.assertEqual({row["hex"] for row in rows}, {"0102", "030405"})

            saved_summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(saved_summary["accepted_unique_seeds"], 2)


if __name__ == "__main__":
    unittest.main()
