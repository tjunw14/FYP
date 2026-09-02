# WebLLM + AFL++ Open5GS Workbench

## Purpose

This is the integrated browser interface for the FYP workflow. It connects the existing browser-local WebLLM seed generator to the controlled local Open5GS/AFL++ backend and the guarded post-fuzzing analysis flow.

The final interaction is:

```text
Load WebLLM
    ↓
Choose configured Open5GS target
    ↓
Generate candidate seeds
    ↓
Preview / validate seeds
    ↓
Start AFL++ fuzzing
    ↓
View live fuzzer_stats
    ↓
Review crash / hang evidence
    ↓
Analyse recorded evidence with WebLLM
    ↓
Export report
```

WebLLM does not replace AFL++. WebLLM supplies local/browser LLM assistance; AFL++ remains the fuzzing engine and the Python backend is the controlled boundary between the webpage and Docker.

## Architecture

```text
Browser
├── WebLLM model (WebGPU)
├── target selector
├── seed generation / preview
├── live statistics
├── guarded result analysis
└── report export
        │
        │ same-origin HTTP API
        ▼
Local Python backend
├── configured target metadata
├── seed validation / clean corpus
├── Docker process manager
├── AFL++ fuzzer_stats reader
├── crash / hang counting
└── evidence / report preparation
        │
        ▼
Docker + AFL++ + Open5GS harness
```

The browser cannot submit arbitrary shell commands. The backend constructs a fixed Docker command for the configured Open5GS Registration Request target.

## Requirements

Before running the UI:

1. Docker Desktop must be running.
2. The repository must contain the existing Open5GS checkout/build under `external/open5gs`.
3. A recent Chrome or Edge browser with WebGPU support should be used.
4. The `aflplusplus/aflplusplus` Docker image should be available (Docker can pull it if required).

The backend installs the small `libtalloc-dev`/`pkg-config` build prerequisites inside the fuzzing container before rebuilding the harness. The harness binary is a generated local artifact and should not be committed.

## Start the integrated workbench on Windows CMD

From the repository root:

```bat
cd C:\Users\tjunw\FYP
set PYTHONPATH=src
py -m fyp_llm_afl.api.server --port 8000
```

Then open:

```text
http://127.0.0.1:8000/webllm_demo/
```

Do **not** use `python -m http.server` for the integrated workflow. A plain static server cannot start AFL++, read live statistics, or export backend evidence.

## Workflow details

### 1. Load WebLLM

Choose a small WebLLM model. The page prefers a small Qwen instruct model when available. Model inference is performed locally in the browser through WebGPU.

### 2. Choose Open5GS target

Target definitions are loaded from `configs/*.json`. The current enabled backend target is:

```text
open5gs_registration_request
ogs_nas_5gs_decode_registration_request()
```

### 3. Generate seeds

WebLLM generates labelled compact hexadecimal lines such as:

```text
seed_001: 4101f000
seed_002: 7e0041012e00
```

### 4. Preview / validate seeds

The browser lets the user review/edit the generated output before sending it to the backend.

The backend then:

- strictly validates labelled hexadecimal seed lines;
- writes only binary `.bin` seed files;
- removes duplicates through `seed_corpus.py`;
- writes a clean corpus and manifest;
- prevents README/CSV files from becoming AFL++ seed inputs.

The clean corpus is stored under:

```text
targets/open5gs/seeds_registration_webllm_clean/
```

### 5. Start fuzzing

The UI supports a short smoke test or the 15-minute demonstration run. The backend starts a named Docker container, rebuilds the existing instrumented Open5GS harness, and invokes `scripts/run_open5gs_fuzz.sh`.

The existing NAS dictionary can optionally be enabled from the UI.

### 6. Live statistics

The page polls the backend every two seconds. The backend reads the AFL++ `fuzzer_stats` file from the mounted output directory and reports values such as:

- runtime;
- executions;
- executions/sec;
- corpus count;
- bitmap coverage;
- edges;
- stability;
- timeouts;
- crashes;
- hangs;
- max depth.

The browser therefore shows the fuzzing progress without requiring the user to inspect the AFL++ terminal directly.

### 7. Analyse with WebLLM

When the run is no longer active, the browser requests a factual evidence bundle from the backend. The backend creates a guarded prompt containing the recorded AFL++ evidence and crash/hang counts.

That prompt is analysed by the same browser-local WebLLM model.

The guardrails state that:

- a crash is not automatically a confirmed vulnerability;
- a no-crash run does not prove that the target is secure;
- conclusions must be based on recorded evidence;
- real vulnerability claims require reproduction, source/sanitizer evidence, and human review;
- exploit instructions are outside the workflow.

### 8. Export report

The report export combines:

- the workflow description;
- validated-seed information;
- factual AFL++ statistics;
- crash/hang counts;
- the WebLLM guarded analysis;
- the interpretation boundary.

A copy is saved under:

```text
reports/open5gs/webllm_ui_run/exported_webllm_fuzzing_report.md
```

and a Markdown copy is downloaded by the browser.

## Backend API

The browser uses these fixed endpoints:

```text
GET  /api/health
GET  /api/targets
POST /api/seeds/validate
POST /api/fuzz/start
POST /api/fuzz/stop
GET  /api/fuzz/status
GET  /api/fuzz/results
GET  /api/triage/evidence
POST /api/report/export
```

There is intentionally no generic command-execution endpoint.

## Reporting interpretation

The WebLLM-driven workflow is evidence that a browser-local small language model can be integrated as an assistant around an AFL++ fuzzing workflow. It should not be reported as evidence that WebLLM itself is a fuzzer or that the local model independently proves vulnerabilities.

If a run records zero crashes and zero hangs, the correct statement is that no crash or hang was observed during that recorded run. It is not proof that Open5GS is vulnerability-free.
