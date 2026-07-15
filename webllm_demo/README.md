# WebLLM-Driven AFL++ Seed Generation Demo

## Purpose

This demo adds a small WebLLM-driven component to the existing LLM-assisted AFL++ fuzzing workflow.

The aim is to show that a browser-based local LLM can generate fuzzing seed inputs that are then passed into the existing AFL++ Open5GS harness.

This supports the edge-device / low-cost local LLM angle of the project.

## Workflow

```text
WebLLM browser demo
        ↓
Generate Open5GS NAS Registration Request seed hex strings
        ↓
Convert hex strings into binary AFL++ seed files
        ↓
Run AFL++ against the existing Open5GS harness
        ↓
Collect fuzzer_stats, crash_count, and hang_count
        ↓
Summarise the WebLLM-driven fuzzing workflow
```

## Requirements

Use a recent browser with WebGPU support, preferably Chrome or Edge.

The first model load may take several minutes because the model files are downloaded and cached by the browser.

## Step 1: Run a local HTTP server

From the repository root on Windows:

```bat
cd C:\Users\tjunw\FYP
python -m http.server 8000
```

Open this in the browser:

```text
http://localhost:8000/webllm_demo/
```

Do not open `index.html` directly as a local file. Use the local HTTP server.

## Step 2: Generate WebLLM seed lines

1. Select a small model from the dropdown.
2. Click `Load selected model`.
3. Wait for the model to finish loading.
4. Click `Generate WebLLM seeds`.
5. Download the parsed output as:

```text
webllm_generated_seeds.txt
```

## Step 3: Save the generated seed transcript

Create the report folder if it does not already exist:

```bat
mkdir reports\open5gs\phase5_webllm_demo
```

Copy the downloaded `webllm_generated_seeds.txt` into:

```text
reports/open5gs/phase5_webllm_demo/webllm_generated_seeds.txt
```

## Step 4: Convert WebLLM hex output into AFL++ binary seed files

Run:

```bat
python scripts\import_webllm_hex_seeds.py --input reports\open5gs\phase5_webllm_demo\webllm_generated_seeds.txt --output targets\open5gs\seeds_registration_webllm --clean
```

Check the generated files:

```bat
dir targets\open5gs\seeds_registration_webllm
```

## Step 5: Run a short AFL++ WebLLM-seed experiment

Use the same Open5GS harness as the previous phases.

A 10 to 15 minute run is sufficient because this phase demonstrates the WebLLM-driven workflow rather than trying to outperform the earlier 30-minute and 2-hour experiments.

Inside the AFL++ Docker container:

```bash
cd /work/targets/open5gs
rm -rf out_registration_webllm_15m
timeout 15m afl-fuzz -i seeds_registration_webllm -o out_registration_webllm_15m -- ./harness_registration_request @@
```

## Step 6: Save AFL++ evidence

Inside Docker:

```bash
mkdir -p /work/reports/open5gs/phase5_webllm_demo
cp out_registration_webllm_15m/default/fuzzer_stats /work/reports/open5gs/phase5_webllm_demo/fuzzer_stats.txt
find out_registration_webllm_15m/default/crashes -type f ! -name README.txt | wc -l > /work/reports/open5gs/phase5_webllm_demo/crash_count.txt
find out_registration_webllm_15m/default/hangs -type f ! -name README.txt | wc -l > /work/reports/open5gs/phase5_webllm_demo/hang_count.txt
```

## Reporting interpretation

Do not claim that WebLLM replaces AFL++.

Correct interpretation:

```text
WebLLM was used as a browser-based local LLM component to generate candidate fuzzing seeds. These seeds were then imported into the existing AFL++ Open5GS fuzzing workflow. This demonstrates how the LLM-assisted seed-generation component can be moved into a local browser or edge-device style environment.
```

If no crashes or hangs are found, report it conservatively:

```text
The WebLLM-driven seed experiment completed without crashes or hangs. This does not prove the target is secure; it only shows that the WebLLM-generated seeds were compatible with the existing AFL++ workflow.
```
