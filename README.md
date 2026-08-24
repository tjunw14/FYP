# Securing Open Source Software using Large Language Models

**Official title:** Securing Open Source Software using Large Language Models: AFL++-Based Fuzzing and Vulnerability Analysis for 5G/6G Network Software

## Project scope

This project builds an LLM-assisted fuzzing and vulnerability analysis framework for open-source 5G/networking software.

The practical target area is **5G network software**, with **Open5GS** as the main target candidate. 6G is used as future/security motivation in the report.

The framework compares:

1. **Baseline AFL++ fuzzing**
   - human/manual seed inputs
   - manually written fuzzing harnesses
   - normal AFL++ crash outputs

2. **LLM-assisted AFL++ fuzzing**
   - LLM-assisted seed generation
   - LLM-assisted harness generation support
   - LLM-assisted crash triage
   - LLM-generated vulnerability explanation reports
   - browser-local WebLLM seed generation and result analysis

## Minimum viable version

The MVP is intentionally small and realistic:

1. Build a working AFL++ fuzzing pipeline.
2. Run AFL++ against a small NAS-like binary parser target as a smoke test.
3. Generate extra seed inputs using a local lightweight LLM.
4. Compare baseline seeds vs LLM-generated seeds.
5. Move the harnessing approach to Open5GS NAS 5GS decoder code.
6. Generate crash triage reports from AFL++ crashes using the LLM.
7. Integrate WebLLM, AFL++, live evidence, guarded triage and report export in one local browser workbench.

## Recommended local LLM

Use **Qwen2.5-Coder 7B Instruct** through Ollama or another local runtime for the desktop/local-LLM experiments.

Default model name used by this repo:

```bash
qwen2.5-coder:7b
```

The Python tools call Ollama's local API at:

```bash
http://localhost:11434/api/chat
```

The final browser demo additionally uses a small WebLLM model through WebGPU.

## Machine split

### MacBook Air M2

Use this mainly for:

- writing Python framework code
- editing harnesses
- generating reports
- pushing/pulling GitHub changes
- light testing

### Windows PC with RTX 2060 Super

Use this mainly for:

- Docker
- AFL++ fuzzing
- local LLM inference
- browser WebLLM demo
- longer fuzzing runs

## Folder structure

```text
FYP/
├── configs/                # Target/workflow metadata
├── docker/                 # Docker files for AFL++/fuzzing environment
├── docs/                   # Architecture and workflow documentation
├── reports/                # Generated crash and experiment reports
├── scripts/                # Setup, build, run, and helper scripts
├── src/fyp_llm_afl/        # Python framework + local API/backend
├── targets/                # Fuzzing targets, harnesses, dictionaries, seeds
│   ├── toy_nas_tlv/        # First AFL++ smoke-test target
│   └── open5gs/            # Main Open5GS NAS fuzzing target
├── tests/                  # Integration helper tests
├── webllm_demo/            # Integrated browser workbench
└── README.md
```

## First AFL++ prototype

The first target is a small NAS-like TLV parser in `targets/toy_nas_tlv`. It is not the final research target. It is used to verify that AFL++, seeds, Docker, scripts, and reporting all work.

From WSL2/Linux:

```bash
cd targets/toy_nas_tlv
make
make fuzz
```

Or using Docker:

```bash
docker compose run --rm afl bash
cd /work/targets/toy_nas_tlv
make
make fuzz
```

## Generate LLM seeds

Make sure Ollama is running and the model is pulled:

```bash
ollama pull qwen2.5-coder:7b
```

Then run:

```bash
python -m fyp_llm_afl.generate_seeds \
  --target toy_nas_tlv \
  --count 10 \
  --out targets/toy_nas_tlv/seeds_llm
```

## Crash report generation

After AFL++ finds crashes, generate a triage report:

```bash
python -m fyp_llm_afl.crash_report \
  --target toy_nas_tlv \
  --crashes targets/toy_nas_tlv/out/default/crashes \
  --out reports/toy_nas_tlv_crash_report.md
```

## Integrated Open5GS architecture

The existing components are connected through one reusable defensive fuzzing pipeline:

```text
Manual / Ollama / WebLLM / protocol-aware seeds
                    |
                    v
          clean seed corpus + manifest
                    |
                    v
          AFL++ Open5GS harness
          + optional NAS dictionary
                    |
                    v
       fuzzer_stats + crash/hang counts
                    |
                    v
         guarded LLM-assisted triage
```

See `docs/architecture.md` for the full design.

## Final browser workbench

The `architecture-integration` branch contains the interactive workflow used for the final demo:

```text
Load WebLLM
    ↓
Choose Open5GS target
    ↓
Generate seeds
    ↓
Preview / validate seeds
    ↓
Start fuzzing
    ↓
Live AFL++ statistics
    ↓
Crash / hang results
    ↓
Analyse with WebLLM
    ↓
Guarded triage
    ↓
Export report
```

### Run on Windows CMD

Docker Desktop must already be running and the existing Open5GS checkout/build must be present under `external/open5gs`.

From the repository root:

```bat
cd C:\Users\tjunw\FYP
set PYTHONPATH=src
py -m fyp_llm_afl.api.server --port 8000
```

Open:

```text
http://127.0.0.1:8000/webllm_demo/
```

Do not use `python -m http.server` for this integrated demo. The custom local server provides the fixed backend API required to start/stop the configured AFL++ run, read live `fuzzer_stats`, provide evidence for WebLLM triage, and export the report.

The browser does not expose arbitrary shell execution. It can only request the configured Open5GS Registration Request workflow.

## Command-line architecture helpers

### Prepare a clean WebLLM corpus

```bash
PYTHONPATH=src python -m fyp_llm_afl.seed_corpus \
  --input targets/open5gs/seeds_registration_webllm \
  --out targets/open5gs/seeds_registration_webllm_clean \
  --clean
```

Only `.bin` files are accepted. The command removes byte-identical duplicates and creates `manifest.csv` and `summary.json`.

### Build the Open5GS harness inside Docker

```bash
bash /work/scripts/build_open5gs_harness.sh
```

The generated harness binary is a local build artifact and should not be committed.

### Run a reproducible 15-minute WebLLM experiment manually

Inside an AFL++ container:

```bash
bash /work/scripts/run_open5gs_fuzz.sh \
  targets/open5gs/seeds_registration_webllm_clean \
  targets/open5gs/out_registration_webllm_architecture_15m \
  15m \
  reports/open5gs/webllm_architecture_15m \
  -
```

To enable the existing NAS dictionary, replace the final `-` with:

```text
targets/open5gs/nas_registration_request.dict
```

The experiment runner stores factual evidence including `fuzzer_stats.txt`, `crash_count.txt`, `hang_count.txt`, `summary.json`, and `summary.md`.

## Result interpretation

A saved AFL++ crash is not automatically a confirmed vulnerability. Reproduce the crash and gather sanitizer/source-code evidence before using the guarded triage framework. Likewise, a no-crash experiment does not prove that Open5GS is secure.

## Final expected deliverables

- GitHub repository with reproducible setup
- AFL++ fuzzing harness and experiment scripts
- baseline vs LLM-assisted fuzzing comparison
- crash analysis reports
- integrated WebLLM/AFL++ browser demo
- final report with methodology, results, limitations, and future 6G relevance
