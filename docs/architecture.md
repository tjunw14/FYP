# Integrated FYP Architecture

## Goal

This architecture keeps the existing project components and connects them into one reproducible defensive fuzzing workflow. It does **not** replace the work already completed for the toy target, Open5GS, Ollama, WebLLM, protocol-aware seeds, or guarded triage.

The main research pipeline is:

```text
                    +-----------------------+
                    |  Seed generation      |
                    |-----------------------|
                    | Manual/baseline       |
                    | Ollama local LLM      |
                    | WebLLM browser model  |
                    | Protocol-aware script |
                    +-----------+-----------+
                                |
                                v
                    +-----------------------+
                    | Seed corpus layer     |
                    |-----------------------|
                    | validate binary files |
                    | remove duplicates     |
                    | create clean corpus   |
                    | write manifest        |
                    +-----------+-----------+
                                |
                                v
+-------------------+   +-----------------------+   +-----------------------+
| Target definition |-->| AFL++ execution       |-->| Evidence collection   |
|-------------------|   |-----------------------|   |-----------------------|
| Open5GS decoder   |   | instrumented harness  |   | fuzzer_stats          |
| harness source    |   | optional AFL dict     |   | crash count           |
| NAS dictionary    |   | timed experiment      |   | hang count            |
+-------------------+   +-----------------------+   | machine-readable JSON |
                                                    +-----------+-----------+
                                                                |
                                                                v
                                                    +-----------------------+
                                                    | Guarded triage/report |
                                                    |-----------------------|
                                                    | source context        |
                                                    | sanitizer evidence    |
                                                    | LLM-assisted analysis |
                                                    | conservative verdict  |
                                                    +-----------------------+
```

## Existing components retained

The architecture deliberately reuses the current repository:

- `targets/open5gs/harness_registration_request.c` — Open5GS AFL++ harness.
- `targets/open5gs/nas_registration_request.dict` — NAS-related AFL++ dictionary.
- `targets/open5gs/seeds_registration_llm/` — existing LLM-assisted corpus.
- `targets/open5gs/seeds_registration_protocol/` — protocol-aware corpus.
- `targets/open5gs/seeds_registration_webllm/` — browser WebLLM corpus.
- `src/fyp_llm_afl/generate_seeds.py` — Ollama-based seed generation.
- `scripts/import_webllm_hex_seeds.py` — WebLLM text-to-binary conversion.
- `src/fyp_llm_afl/triage/crash_triage.py` — guarded crash/no-crash triage.
- `reports/` — experiment evidence and report material.

## New integration layer

### 1. Target configuration

`configs/open5gs_registration.json` records the paths and research metadata for the main target. The configuration makes the workflow easier to explain and reproduce without hard-coding the target description in several places.

### 2. Seed corpus preparation

`src/fyp_llm_afl/seed_corpus.py` creates a clean AFL++ input corpus from one or more existing seed directories. It:

- reads only `.bin` files;
- rejects empty or excessively large files;
- removes byte-identical duplicates;
- writes sequential seed names;
- records origin, size, SHA-256 and hexadecimal bytes in `manifest.csv`;
- writes a small `summary.json`.

This also prevents files such as `README.md` and `manifest.csv` from accidentally being treated as AFL++ input seeds.

### 3. AFL++ experiment runner

`scripts/run_open5gs_fuzz.sh` is the reproducible Docker-side runner. It:

- verifies that the Open5GS harness and seed corpus exist;
- creates a temporary binary-only input directory;
- optionally enables the existing AFL++ NAS dictionary;
- runs a time-bounded AFL++ experiment;
- preserves the normal AFL++ output directory;
- calls the result collector to create concise evidence files.

### 4. Result collection

`src/fyp_llm_afl/results.py` converts AFL++ `fuzzer_stats` plus crash/hang directories into:

- `fuzzer_stats.txt` — copied raw AFL++ evidence;
- `crash_count.txt`;
- `hang_count.txt`;
- `summary.json` — machine-readable metrics;
- `summary.md` — report-ready factual summary.

The collector does not interpret a crash as a vulnerability. It only records observed fuzzing evidence.

### 5. Guarded LLM triage

The existing `src/fyp_llm_afl/triage/crash_triage.py` remains the analysis layer. A saved crash should first be reproduced and supported by source/sanitizer evidence before the LLM-generated analysis is used in the report.

## Recommended experiment flow

For each experiment:

1. Choose one seed source or combination of sources.
2. Prepare a clean corpus with `seed_corpus.py`.
3. Build/reuse the instrumented Open5GS harness.
4. Run `run_open5gs_fuzz.sh` for a fixed duration.
5. Save the generated evidence under `reports/open5gs/<experiment-name>/`.
6. If a crash exists, reproduce it and collect sanitizer/source evidence.
7. Run guarded triage.
8. Compare only experiments that have compatible settings, especially AFL++ version and duration.

## Example: WebLLM integration

```text
WebLLM browser
   -> webllm_generated_seeds.txt
   -> scripts/import_webllm_hex_seeds.py
   -> targets/open5gs/seeds_registration_webllm/*.bin
   -> seed_corpus.py
   -> AFL++ Open5GS harness
   -> results.py
   -> guarded triage/reporting
```

This makes WebLLM one interchangeable seed provider inside the same pipeline rather than a separate fuzzing system.

## Research boundaries

- The workflow is for defensive testing of the selected Open5GS parser target.
- A no-crash run does not prove that Open5GS is secure.
- A saved AFL++ crash is not automatically a confirmed vulnerability.
- The toy target's intentional abort remains a controlled validation event, not a real vulnerability.
- LLM output is supporting evidence and report assistance; final security conclusions require human verification.
