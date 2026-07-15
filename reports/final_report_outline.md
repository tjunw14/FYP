# Final FYP Report Outline

## Working Title

**Securing Open Source Software using Large Language Models: AFL++-Based Fuzzing and Vulnerability Analysis for 5G/6G Network Software**

## Purpose of This Outline

This document provides the recommended structure for the final FYP report. It maps the implemented project phases to report chapters and identifies which evidence files should be used in each section.

---

# Recommended Report Structure

## Abstract

Summarise the project in one concise paragraph:

- Problem: open-source network software can contain parser and protocol-handling bugs.
- Approach: combine AFL++ fuzzing with LLM-assisted seed generation, WebLLM/local LLM seed generation, and vulnerability triage.
- Targets: toy NAS-like TLV parser and Open5GS NAS 5GS Registration Request decoder.
- Results: toy target validated the pipeline; Open5GS fuzzing remained stable with no crashes; LLM-assisted seeds and dictionary support showed mixed metric improvements; WebLLM showed a local/browser seed-generation workflow; LLM triage worked best with source-code context and guardrails.
- Conclusion: LLMs are useful assistants for fuzzing workflows but should not be treated as autonomous vulnerability classifiers.

---

## 1. Introduction

### 1.1 Background

Explain why fuzzing is important for open-source and network software security. Mention that protocol parsers are useful targets because they process structured, potentially attacker-controlled inputs.

### 1.2 Motivation

Explain why LLMs are relevant:

- generating seed inputs
- reasoning about protocol structures
- assisting with crash triage
- summarising fuzzing evidence
- enabling local/browser-based fuzzing assistance through WebLLM

Also mention the risk: LLMs can overclaim vulnerability impact if not constrained by evidence.

### 1.3 Project Aim

The aim of this project is to evaluate whether LLMs can assist AFL++ fuzzing and vulnerability analysis for open-source 5G network software, including both local desktop LLM and browser-based WebLLM seed-generation workflows.

### 1.4 Objectives

Suggested objectives:

1. Build an AFL++ fuzzing workflow for a controlled toy target.
2. Apply AFL++ fuzzing to a real Open5GS NAS decoder.
3. Compare baseline seed fuzzing against LLM-assisted seed fuzzing.
4. Build a guarded LLM-assisted triage framework.
5. Explore protocol-aware seeds and AFL++ dictionary support.
6. Add a WebLLM-driven local/browser seed-generation workflow.
7. Evaluate whether LLM assistance improves fuzzing or analysis outcomes.

### 1.5 Scope

State that the project focuses on defensive fuzzing and analysis. It does not attempt exploitation. Open5GS is used as a practical 5G NAS parser target. WebLLM is used as a local/browser LLM demonstration, not as a replacement for AFL++.

---

## 2. Background and Related Work

### 2.1 Fuzz Testing

Explain fuzzing, seed corpus, mutation, coverage-guided fuzzing, crashes, hangs, and corpus growth.

### 2.2 AFL++

Explain why AFL++ was selected:

- coverage-guided fuzzing
- instrumentation
- corpus evolution
- crash and hang reporting
- dictionary support

### 2.3 Open5GS and NAS 5G Parsing

Explain Open5GS as an open-source 5G core implementation. Introduce NAS 5G Registration Request decoding as the selected parser target.

### 2.4 Large Language Models in Security Testing

Discuss possible uses:

- seed generation
- protocol-aware input suggestions
- triage support
- report generation

Also discuss limitations:

- hallucination risk
- overclaiming vulnerability impact
- need for source-code evidence and manual review

### 2.5 WebLLM and Local Small Language Models

Introduce WebLLM as a browser-based local LLM framework that can run small models locally in the browser. Explain why this is relevant to edge-device or lower-cost workflows: it reduces dependence on cloud-hosted LLM services and shows how seed generation could be moved closer to the testing device.

---

## 3. Methodology

### 3.1 Overall Workflow

Describe the full workflow:

1. Select target.
2. Build AFL++ harness.
3. Prepare baseline, LLM-assisted, protocol-aware, and WebLLM-generated seeds.
4. Run AFL++ experiments.
5. Collect `fuzzer_stats`, crash counts, and hang counts.
6. Compare metrics.
7. Perform guarded LLM-assisted triage.
8. Interpret results conservatively.

### 3.2 Experimental Environment

Include:

- AFL++ Docker environment
- AFL++ versions used: `++4.41a` for Phase 1/2 and `++5.02a` for Phase 4/5
- Open5GS build with AFL++ instrumentation
- Ollama model: `qwen2.5-coder:7b`
- WebLLM browser demo with a small local model
- Windows PC for Docker/AFL++ and browser WebLLM execution
- MacBook for coding/reporting and lightweight generation tasks

### 3.3 Metrics Collected

Explain key metrics:

- runtime
- executions
- executions per second
- corpus count
- corpus found
- corpus favored
- max depth
- bitmap coverage
- edges found
- saved crashes
- saved hangs
- total timeouts
- stability

### 3.4 Reporting Rules

Include the conservative reporting policy:

- A crash is not automatically a vulnerability.
- A no-crash run does not prove the target is secure.
- Toy target crashes must not be reported as real vulnerabilities.
- LLM-generated conclusions require human review.
- WebLLM output is treated as generated seed input evidence, not as a security verdict.

---

## 4. Implementation

### 4.1 Repository Structure

Discuss the main folders:

- `targets/toy_nas_tlv/`
- `targets/open5gs/`
- `scripts/`
- `prompts/`
- `reports/`
- `src/fyp_llm_afl/triage/`
- `webllm_demo/`

### 4.2 Toy Target Implementation

Describe the toy NAS-like TLV parser and its intentional `abort()` path.

Evidence files:

- `targets/toy_nas_tlv/toy_nas_tlv.c`
- `reports/toy_nas_tlv/comparison.csv`

### 4.3 Open5GS Harness Implementation

Describe the Open5GS harness:

- reads input file
- wraps bytes into `ogs_pkbuf_t`
- initialises `ogs_nas_5gs_message_t`
- calls `ogs_nas_5gs_decode_registration_request()`

Evidence files:

- `targets/open5gs/harness_registration_request.c`
- `reports/open5gs/harness_registration_request.c.txt`

### 4.4 LLM-Assisted Seed Generation

Discuss how LLM-assisted seed corpora were generated and used.

### 4.5 Guarded Triage Framework

Discuss:

- `src/fyp_llm_afl/triage/crash_triage.py`
- `prompts/crash_triage_prompt_template.md`
- generated triage reports
- generated LLM prompts and outputs

### 4.6 Protocol-Aware Seeds and Dictionary

Discuss:

- `scripts/generate_open5gs_registration_seeds.py`
- `targets/open5gs/nas_registration_request.dict`
- `targets/open5gs/seeds_registration_protocol/`

### 4.7 WebLLM-Driven Seed Generation Demo

Discuss:

- `webllm_demo/index.html`
- `webllm_demo/webllm_seed_prompt.md`
- `webllm_demo/webllm_generated_seeds.txt`
- `scripts/import_webllm_hex_seeds.py`
- `targets/open5gs/seeds_registration_webllm/`

Explain that WebLLM generated hexadecimal seed lines in the browser. These were converted into binary AFL++ seed files and then used with the existing Open5GS harness.

---

## 5. Experiments and Results

### 5.1 Phase 1: Toy NAS-like TLV Parser

Use:

- `reports/final_project_summary.md`
- `reports/toy_nas_tlv/comparison.csv`

Key conclusion:

The LLM-generated seeds discovered the intentional toy crash, validating the pipeline, but this was not a real vulnerability.

### 5.2 Phase 2A: Open5GS Harness Smoke Test

Use:

- `reports/open5gs/registration_harness_smoke_fuzzer_stats.txt`

Key conclusion:

The harness successfully reached the Open5GS NAS Registration Request decoder and remained stable.

### 5.3 Phase 2B/2C: Open5GS 30-Minute Baseline vs LLM-Assisted Run

Use:

- `reports/open5gs/phase2d_comparison/open5gs_baseline_vs_llm.csv`
- `reports/open5gs/phase2d_comparison/open5gs_phase2_report_summary.md`

Key conclusion:

The LLM-assisted run improved executions, corpus growth, depth, and timeouts, but did not improve coverage or discover vulnerabilities.

### 5.4 Phase 2E/2F: Open5GS Two-Hour Comparison

Use:

- `reports/open5gs/phase2e_2h_comparison/open5gs_2h_baseline_vs_llm.csv`
- `reports/open5gs/phase2e_2h_comparison/open5gs_2h_report_summary.md`

Key conclusion:

Both runs reached the same coverage and edge count. The LLM-assisted run had a slightly larger corpus and greater depth, but the baseline had higher throughput and fewer timeouts. No crashes or hangs were found.

### 5.5 Phase 3: LLM-Assisted Triage

Use:

- `reports/phase3_triage/phase3e_triage_evaluation.md`
- `reports/phase3_triage/README.md`

Key conclusion:

The LLM correctly classified the toy crash as intentional and Open5GS as a no-crash result when given guardrails and source-code context. Human review remains necessary.

### 5.6 Phase 4: Protocol-Aware Seeds and AFL++ Dictionary

Use:

- `reports/open5gs/phase4_comparison/open5gs_phase4_comparison.csv`
- `reports/open5gs/phase4_comparison/open5gs_phase4_report_summary.md`

Key conclusion:

The dictionary run found one additional edge and slightly increased bitmap coverage, but reduced throughput and corpus growth. No crashes or hangs were found.

### 5.7 Phase 5: WebLLM-Driven Seed Generation Demo

Use:

- `reports/open5gs/phase5_webllm_15m/fuzzer_stats.txt`
- `reports/open5gs/phase5_webllm_15m/webllm_15m_report_summary.md`
- `webllm_demo/webllm_generated_seeds.txt`
- `targets/open5gs/seeds_registration_webllm/manifest.csv`

Key conclusion:

The WebLLM-generated seeds were converted into binary AFL++ seed files and successfully used with the Open5GS harness. The 15-minute run completed with 113,325 executions, 2.99% bitmap coverage, 320 discovered edges, 0 crashes, 0 hangs, and 100.00% stability. This demonstrates WebLLM as a browser/local LLM seed-generation component, not as a vulnerability discovery result.

---

## 6. Discussion

### 6.1 Effectiveness of LLM-Assisted Seeds

Discuss that LLM-assisted seeds were valid and sometimes improved secondary metrics, but did not consistently improve coverage.

### 6.2 Importance of Experiment Duration

Discuss how 30-minute results looked more favourable to LLM-assisted seeds than the two-hour results.

### 6.3 LLM Triage Strengths

Discuss how source-code context helped prevent overclaiming.

### 6.4 LLM Triage Limitations

Mention the Open5GS LLM output phrase that was slightly too confident.

### 6.5 Protocol-Aware Seeds and Dictionary Support

Discuss the small coverage improvement from dictionary support and the tradeoff in efficiency.

### 6.6 WebLLM and Edge-Device Relevance

Discuss how WebLLM demonstrates a local/browser LLM seed-generation workflow. Explain that this supports the edge-device or lower-cost LLM angle because seed generation can occur locally rather than through cloud services. Also state that the WebLLM experiment was a workflow demonstration, not a full benchmark against the longer AFL++ runs.

---

## 7. Limitations

Suggested limitations:

1. Only one Open5GS NAS decoder function was fuzzed.
2. No real Open5GS vulnerabilities were discovered.
3. LLM-generated seed quality was limited by prompt design and protocol knowledge.
4. Phase 4 and Phase 5 used a different AFL++ version than Phase 2.
5. Fuzzing duration was limited to 15-minute, 30-minute, and two-hour runs.
6. The WebLLM run was a small workflow demonstration, not a full performance comparison.
7. The LLM triage framework still requires human review.
8. The harness targets message body decoding rather than the complete network stack path.

---

## 8. Future Work

Suggested future work:

1. Fuzz additional Open5GS NAS message decoders.
2. Build more accurate NAS message templates.
3. Improve LLM seed generation using source-code-guided prompts.
4. Add structured ASN.1/NAS field-aware mutation strategies.
5. Run longer multi-hour or overnight AFL++ campaigns.
6. Integrate sanitizer output collection directly into the triage framework.
7. Extend the approach toward Linux kernel networking or 5G/6G edge networking targets.
8. Explore stronger WebLLM models and on-device browser fuzzing assistants.

---

## 9. Conclusion

The conclusion should state:

- The project successfully built an end-to-end LLM-assisted AFL++ fuzzing workflow.
- The workflow was validated on a toy parser and applied to Open5GS.
- LLM-assisted seeds were valid but did not consistently improve coverage.
- LLM-assisted triage was useful when constrained by source-code context and guardrails.
- WebLLM demonstrated a browser/local LLM seed-generation path for lower-cost or edge-device-oriented workflows.
- No real vulnerabilities were discovered.
- The main contribution is a practical workflow combining seed generation, fuzzing, triage, WebLLM integration, and conservative reporting.

---

## Appendices

Suggested appendices:

- Appendix A: Full AFL++ fuzzer statistics
- Appendix B: Seed corpus examples
- Appendix C: AFL++ dictionary
- Appendix D: Harness source code
- Appendix E: LLM prompts and outputs
- Appendix F: WebLLM demo files and generated seeds
- Appendix G: GitHub repository structure
