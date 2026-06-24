# Final Project Summary: LLM-Assisted AFL++ Fuzzing and Vulnerability Analysis

## Project Title

**Securing Open Source Software using Large Language Models: AFL++-Based Fuzzing and Vulnerability Analysis for 5G/6G Network Software**

## Project Overview

This project investigates how large language models can support fuzzing workflows for open-source network software. The work combines AFL++ fuzzing with LLM-assisted seed generation, protocol-aware input preparation, and guarded vulnerability triage.

The project was developed in progressive phases. It started with a controlled toy NAS-like TLV parser to validate the fuzzing pipeline, then moved to a real Open5GS NAS 5GS Registration Request decoder target. Later phases added LLM-assisted triage, no-crash result interpretation, protocol-aware seed generation, and AFL++ dictionary support.

The main goal is not to claim that an LLM can autonomously find or verify vulnerabilities. Instead, the project evaluates where LLMs can assist the fuzzing workflow while still requiring source-code evidence, reproducible fuzzing results, and human review.

---

## Phase Overview

| Phase | Status | Main Purpose |
|---|---|---|
| Phase 1 | Completed | Validate AFL++ + LLM seed-generation pipeline using a controlled toy target |
| Phase 2 | Completed | Fuzz real Open5GS NAS parser code and compare baseline vs LLM-assisted seeds |
| Phase 3 | Completed | Add LLM-assisted crash/no-crash triage and guarded vulnerability-analysis workflow |
| Phase 4 | Completed | Improve Open5GS fuzzing attempt with protocol-aware seeds and AFL++ dictionary support |
| Phase 5 | In progress | Consolidate final results for report writing |

---

# Phase 1: Toy NAS-like TLV Parser Validation

## Purpose

Phase 1 used a toy NAS-like TLV parser to validate the end-to-end AFL++ and LLM-assisted fuzzing workflow. The toy target intentionally contained an `abort()` condition so that the pipeline could be tested with a known crash outcome.

The key purpose was to verify that:

1. Manual and LLM-generated seeds could be passed to AFL++.
2. AFL++ could discover a known crash condition.
3. The project could collect fuzzer statistics, crash counts, and report data.
4. LLM triage must be guarded to avoid overclaiming controlled crashes as real vulnerabilities.

## Phase 1 Results

| Metric | Baseline Manual Seeds | LLM-Generated Seeds |
|---|---:|---:|
| Runtime | 782 s | 784 s |
| Executions | 103,790 | 106,106 |
| Executions/sec | 132.60 | 135.20 |
| Corpus count | 50 | 53 |
| Corpus found | 47 | 48 |
| Corpus favored | 15 | 14 |
| Max depth | 7 | 7 |
| Bitmap coverage | 33.33% | 33.33% |
| Edges found | 24 / 72 | 24 / 72 |
| Saved crashes | 0 | 1 |
| Saved hangs | 0 | 0 |
| Total timeouts | 15 | 13 |
| Stability | 100.00% | 100.00% |

## Phase 1 Interpretation

The LLM-generated seed run discovered one saved crash, while the baseline did not. However, this crash was caused by an intentional `abort()` condition in the toy target and must not be reported as a real vulnerability.

Phase 1 demonstrated that LLM-generated seeds can be valid AFL++ inputs and can help reach specific parser behaviours. It also showed the risk of LLM overclaiming: without source-code context, a crash could be incorrectly described as a real vulnerability. This motivated the later Phase 3 guarded triage framework.

---

# Phase 2: Open5GS AFL++ Fuzzing Comparison

## Purpose

Phase 2 moved from the toy target to real open-source 5G software. The selected target was the Open5GS NAS 5GS Registration Request decoder:

`ogs_nas_5gs_decode_registration_request()`

A custom AFL++ harness, `harness_registration_request`, was implemented to pass AFL++ input bytes into the Open5GS decoder. The harness treats fuzzing input as the body of a Registration Request message.

## Phase 2A: Harness Smoke Test

| Metric | Result |
|---|---:|
| Runtime | 121 s |
| Executions | 20,611 |
| Executions/sec | 169.23 |
| Corpus count | 132 |
| Corpus found | 129 |
| Corpus favored | 53 |
| Max depth | 3 |
| Bitmap coverage | 2.49% |
| Edges found | 267 / 10,706 |
| Saved crashes | 0 |
| Saved hangs | 0 |
| Total timeouts | 0 |
| Stability | 100.00% |

The smoke test confirmed that the Open5GS harness executed successfully and reached the target NAS decoder.

## Phase 2B/2C: 30-Minute Baseline vs LLM-Assisted Fuzzing

| Metric | Baseline 30m | LLM-Assisted 30m |
|---|---:|---:|
| Runtime | 1798 s | 1797 s |
| Executions | 210,442 | 234,895 |
| Executions/sec | 117.00 | 130.65 |
| Corpus count | 348 | 371 |
| Corpus found | 345 | 351 |
| Corpus favored | 118 | 117 |
| Max depth | 8 | 9 |
| Bitmap coverage | 3.00% | 2.99% |
| Edges found | 321 / 10,706 | 320 / 10,706 |
| Saved crashes | 0 | 0 |
| Saved hangs | 0 | 0 |
| Total timeouts | 312 | 133 |
| Stability | 100.00% | 100.00% |

## 30-Minute Interpretation

The LLM-assisted run executed more test cases, produced a larger corpus, reached slightly greater max depth, and had fewer timeouts. However, it did not improve edge coverage and found no crashes or hangs.

This result showed that the LLM-assisted seed corpus was valid and stable, but did not demonstrate vulnerability discovery or a clear coverage advantage.

## Phase 2E: Two-Hour Baseline vs LLM-Assisted Fuzzing

| Metric | Baseline 2h | LLM-Assisted 2h |
|---|---:|---:|
| Runtime | 7198 s | 7197 s |
| Executions | 892,769 | 855,466 |
| Executions/sec | 124.02 | 118.85 |
| Corpus count | 448 | 454 |
| Corpus found | 445 | 434 |
| Corpus favored | 109 | 103 |
| Max depth | 10 | 11 |
| Bitmap coverage | 3.01% | 3.01% |
| Edges found | 322 / 10,706 | 322 / 10,706 |
| Saved crashes | 0 | 0 |
| Saved hangs | 0 | 0 |
| Total timeouts | 181 | 279 |
| Stability | 100.00% | 100.00% |

## Two-Hour Interpretation

The two-hour experiment showed a more balanced result. The LLM-assisted run produced a slightly larger corpus and reached a greater maximum depth, but the baseline executed more test cases and had fewer timeouts.

Both runs achieved the same bitmap coverage and discovered the same number of edges. Neither run found crashes or hangs.

The careful conclusion is that LLM-assisted seeds remained valid and stable for longer fuzzing, but did not produce a clear coverage advantage over the baseline in this Open5GS experiment.

---

# Phase 3: LLM-Assisted Fuzzing Result Triage

## Purpose

Phase 3 addressed the vulnerability-analysis part of the project. It implemented a guarded triage workflow to analyse fuzzing outcomes using structured evidence, source-code context, and LLM prompts.

The goal was to determine whether an LLM can help interpret fuzzing results without overclaiming vulnerability impact.

## Implemented Components

| Component | Path |
|---|---|
| Guarded triage script | `src/fyp_llm_afl/triage/crash_triage.py` |
| LLM triage prompt template | `prompts/crash_triage_prompt_template.md` |
| Toy crash triage report | `reports/phase3_triage/toy_nas_tlv/toy_crash_triage_report.md` |
| Toy LLM triage output | `reports/phase3_triage/toy_nas_tlv/toy_llm_triage_output.md` |
| Open5GS no-crash triage report | `reports/phase3_triage/open5gs/open5gs_no_crash_triage_report.md` |
| Open5GS LLM triage output | `reports/phase3_triage/open5gs/open5gs_llm_triage_output.md` |
| Phase 3 evaluation | `reports/phase3_triage/phase3e_triage_evaluation.md` |
| Phase 3 README | `reports/phase3_triage/README.md` |

## Phase 3 Cases

| Case | Expected Classification | LLM Output Assessment |
|---|---|---|
| Toy NAS-like TLV crash | Intentional validation crash, not a real vulnerability | Correctly classified and avoided overclaiming |
| Open5GS no-crash run | Stable no-crash fuzzing result, not vulnerability discovery | Correctly classified, with one slightly overconfident phrase |

## Phase 3 Interpretation

Phase 3 showed that LLMs can support fuzzing-result interpretation when given source-code context and strict guardrails. The LLM correctly classified the toy target crash as an intentional validation crash and correctly classified the Open5GS result as a no-crash fuzzing outcome.

However, the Open5GS output also showed that human review remains necessary. Even when the LLM avoids major overclaiming, its wording can still be slightly too confident for a formal security report.

The main conclusion is that the LLM should be framed as an assistant for source-code-aware triage and report generation, not as an autonomous vulnerability classifier.

---

# Phase 4: Protocol-Aware Seeds and AFL++ Dictionary Support

## Purpose

Phase 4 attempted to improve Open5GS fuzzing effectiveness after Phase 2 showed no clear coverage advantage from the initial LLM-assisted seeds.

Two improvements were added:

1. Protocol-aware Open5GS Registration Request seed generation.
2. An AFL++ dictionary containing NAS-related byte tokens.

## Implemented Components

| Component | Path |
|---|---|
| Protocol-aware seed generator | `scripts/generate_open5gs_registration_seeds.py` |
| AFL++ NAS dictionary | `targets/open5gs/nas_registration_request.dict` |
| Protocol-aware seed corpus | `targets/open5gs/seeds_registration_protocol/` |
| Phase 4 comparison summary | `reports/open5gs/phase4_comparison/open5gs_phase4_report_summary.md` |

## Important Caveat

Phase 4 used AFL++ `++5.02a`, while Phase 2 used AFL++ `++4.41a`. Therefore, comparisons between Phase 2 and Phase 4 should be treated as exploratory rather than perfectly controlled. The most direct Phase 4 comparison is between the two Phase 4 runs, since both used AFL++ `++5.02a`.

## Phase 4 Results

| Metric | Phase 4 Protocol Seeds 30m | Phase 4 Protocol Seeds + Dictionary 30m |
|---|---:|---:|
| AFL++ version | ++5.02a | ++5.02a |
| Runtime | 1797 s | 1797 s |
| Executions | 207,409 | 193,281 |
| Executions/sec | 115.36 | 107.50 |
| Corpus count | 377 | 354 |
| Corpus found | 357 | 334 |
| Corpus favored | 110 | 111 |
| Max depth | 6 | 5 |
| Bitmap coverage | 3.00% | 3.01% |
| Edges found | 321 / 10,707 | 322 / 10,707 |
| Saved crashes | 0 | 0 |
| Saved hangs | 0 | 0 |
| Total timeouts | 87 | 102 |
| Stability | 100.00% | 100.00% |

## Phase 4 Interpretation

The AFL++ dictionary produced a small coverage-related improvement: the dictionary run discovered one additional edge and increased bitmap coverage from 3.00% to 3.01%.

However, the dictionary run also reduced throughput, produced a smaller corpus, reached lower maximum depth, and had more timeouts. Therefore, the Phase 4 result is mixed.

The careful conclusion is that dictionary-guided mutation showed a small coverage benefit, but did not clearly improve overall fuzzing efficiency in the 30-minute experiment.

No crashes or hangs were found in Phase 4.

---

# Overall Results Summary

| Experiment | Best Result / Observation | Vulnerability Found? |
|---|---|---|
| Phase 1 toy target | LLM seeds triggered the known intentional SIGABRT crash | No real vulnerability; intentional validation crash |
| Phase 2 Open5GS 30m | LLM-assisted run improved executions, corpus count, depth, and timeouts but not coverage | No |
| Phase 2 Open5GS 2h | Both runs reached same coverage and edges; LLM run had slightly larger corpus and higher depth | No |
| Phase 3 triage | LLM correctly classified toy crash and Open5GS no-crash result with guardrails | No vulnerability claim |
| Phase 4 dictionary | Dictionary run found one additional edge and slightly higher coverage, but lower efficiency | No |

---

# Key Findings

## 1. LLM-generated seeds can be valid AFL++ inputs

The toy target and Open5GS experiments showed that LLM-generated or LLM-assisted seeds can be accepted by AFL++ and used in real fuzzing workflows.

## 2. LLM-assisted seeds did not consistently improve coverage

In Open5GS, the LLM-assisted seeds improved some metrics such as corpus growth, depth, and timeouts in some runs, but did not consistently improve coverage or edge discovery.

## 3. Longer fuzzing reduced the apparent advantage of LLM-assisted seeds

The 30-minute Open5GS run showed stronger LLM-assisted performance in throughput and timeouts. The two-hour run showed a more balanced outcome, with the baseline executing more cases and both runs reaching the same coverage.

## 4. LLM-assisted triage requires source-code context and guardrails

Phase 3 showed that the LLM could correctly classify an intentional toy crash and a no-crash Open5GS result when given structured evidence and explicit rules. Without such guardrails, LLMs may overclaim fuzzing results.

## 5. Dictionary support produced a small coverage improvement but not a clear efficiency improvement

The Phase 4 dictionary run discovered one additional edge and slightly improved bitmap coverage, but had lower throughput and smaller corpus growth.

---

# Limitations

1. Open5GS fuzzing focused on one NAS decoder function rather than the entire Open5GS system.
2. No real vulnerabilities were discovered in the Open5GS experiments.
3. The LLM-assisted seed generation was relatively simple and could be improved with deeper protocol modelling.
4. Phase 4 used a newer AFL++ Docker image than Phase 2, so cross-phase comparisons are exploratory.
5. The fuzzing runs were limited to 30-minute and two-hour windows.
6. The LLM triage workflow still requires human review before any security conclusion is made.

---

# Final Project Conclusion

This project demonstrates an end-to-end workflow for LLM-assisted fuzzing and vulnerability analysis using AFL++. The workflow was validated first on a controlled toy NAS-like TLV parser and then applied to real Open5GS NAS 5G parser code.

The experiments show that LLMs can assist fuzzing workflows by generating valid seed inputs and helping explain fuzzing outcomes when provided with structured evidence and source-code context. However, the results also show that LLM assistance does not automatically produce better coverage or vulnerability discovery. In the Open5GS experiments, LLM-assisted seeds and dictionary-guided mutation produced some improvements in selected metrics, but no crashes or hangs were found.

The strongest contribution of the project is the complete workflow: LLM-assisted seed generation, AFL++ fuzzing, Open5GS harness development, experiment comparison, guarded LLM triage, and conservative reporting. The project shows that LLMs are useful as assistants in fuzzing and vulnerability analysis, but their outputs must be constrained by evidence and reviewed by humans before making security claims.
