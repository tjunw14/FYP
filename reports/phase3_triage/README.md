# Phase 3: LLM-Assisted Fuzzing Result Triage

## Overview

Phase 3 adds the vulnerability-analysis component of the project. Earlier phases focused on AFL++ fuzzing and seed comparison. Phase 3 focuses on whether an LLM can help interpret fuzzing results safely when provided with structured evidence, source-code context, and strict guardrails.

The main goal is not to let the LLM autonomously declare vulnerabilities. Instead, the LLM is used as an assistant for source-code-aware triage and report generation.

## Purpose

The Phase 3 triage framework is designed to handle two cases:

1. A crash is found by AFL++.
2. No crash or hang is found by AFL++.

For both cases, the framework should avoid unsupported vulnerability claims. It should classify results conservatively and clearly separate confirmed evidence from interpretation.

## Implemented Components

| Component | Path | Purpose |
|---|---|---|
| Guarded triage script | src/fyp_llm_afl/triage/crash_triage.py | Generates conservative triage reports and LLM-ready prompts |
| LLM prompt template | prompts/crash_triage_prompt_template.md | Provides strict instructions and guardrails for LLM-based triage |
| Toy crash triage report | reports/phase3_triage/toy_nas_tlv/toy_crash_triage_report.md | Script-generated report for the intentional toy crash |
| Toy LLM prompt | reports/phase3_triage/toy_nas_tlv/toy_llm_triage_prompt.md | Prompt used for LLM triage of the toy crash |
| Toy LLM output | reports/phase3_triage/toy_nas_tlv/toy_llm_triage_output.md | Actual LLM response for the toy crash |
| Open5GS no-crash triage report | reports/phase3_triage/open5gs/open5gs_no_crash_triage_report.md | Script-generated report for Open5GS no-crash run |
| Open5GS LLM prompt | reports/phase3_triage/open5gs/open5gs_llm_triage_prompt.md | Prompt used for LLM triage of Open5GS no-crash result |
| Open5GS LLM output | reports/phase3_triage/open5gs/open5gs_llm_triage_output.md | Actual LLM response for Open5GS no-crash result |
| Phase 3 evaluation | reports/phase3_triage/phase3e_triage_evaluation.md | Human evaluation of LLM outputs against expected classifications |

## Case 1: Toy NAS-like TLV Target

The toy target contains an intentional abort() condition. AFL++ discovered one saved crash during the LLM-assisted seed run.

Correct classification:

| Field | Classification |
|---|---|
| Crash observed | Yes |
| Crash signal | SIGABRT |
| Root cause | Intentional abort condition |
| Real vulnerability | No |
| Purpose | Pipeline validation |

The LLM correctly classified this as an intentional validation crash and avoided unsupported claims such as buffer overflow, integer overflow, remote code execution, or confirmed denial-of-service vulnerability.

## Case 2: Open5GS Registration Request Decoder

The Open5GS two-hour LLM-assisted fuzzing run completed with no crashes or hangs.

Key result:

| Metric | Result |
|---|---:|
| Runtime | 7197 seconds |
| Executions | 855,466 |
| Bitmap coverage | 3.01% |
| Edges found | 322 / 10,706 |
| Saved crashes | 0 |
| Saved hangs | 0 |
| Stability | 100.00% |

Correct classification:

| Field | Classification |
|---|---|
| Crash observed | No |
| Hang observed | No |
| Real vulnerability discovered | No |
| Interpretation | Stable fuzzing evidence |

The LLM correctly classified the Open5GS result as a no-crash fuzzing result and avoided claiming vulnerability discovery. However, it used one slightly overconfident phrase, stating that the function was “functioning correctly with the provided seeds.” A more cautious phrasing would be that the available fuzzing evidence did not trigger crashes or hangs with the provided seeds.

## Key Learning

Phase 3 shows that LLM-assisted vulnerability analysis requires both source-code context and strict guardrails.

Without source-code context, an LLM may overclaim a fuzzing crash as a buffer overflow, integer overflow, denial of service, or remote code execution. With source-code evidence and explicit instructions, the LLM correctly classified the toy crash as an intentional validation crash and correctly classified the Open5GS result as a no-crash fuzzing outcome.

However, LLM output still requires human review. Even when the model avoids major overclaiming, wording may still be too confident for a formal security report.

## Reproducibility

### Generate toy crash triage report and LLM prompt

bash python3 src/fyp_llm_afl/triage/crash_triage.py \   --target-name toy_nas_tlv \   --crash-type "SIGABRT from intentional abort condition" \   --fuzzer-stats reports/toy_nas_tlv/llm_fuzzer_stats.txt \   --source-context targets/toy_nas_tlv/toy_nas_tlv.c \   --notes "This toy target contains an intentional abort condition. The crash is used to validate the AFL++ and LLM-assisted triage pipeline. It must not be reported as a real vulnerability." \   --output reports/phase3_triage/toy_nas_tlv/toy_crash_triage_report.md \   --prompt-template prompts/crash_triage_prompt_template.md \   --prompt-output reports/phase3_triage/toy_nas_tlv/toy_llm_triage_prompt.md 

### Generate Open5GS no-crash triage report and LLM prompt

bash python3 src/fyp_llm_afl/triage/crash_triage.py \   --target-name open5gs_registration_request \   --crash-type "No crash or hang observed" \   --fuzzer-stats reports/open5gs/phase2e_2h_llm/fuzzer_stats.txt \   --harness-code targets/open5gs/harness_registration_request.c \   --source-context reports/open5gs/phase2e_2h_comparison/open5gs_2h_report_summary.md \   --notes "The Open5GS two-hour LLM-assisted fuzzing run completed with 100% stability and found 0 crashes and 0 hangs. This result should be interpreted as stable fuzzing evidence, not vulnerability discovery." \   --output reports/phase3_triage/open5gs/open5gs_no_crash_triage_report.md \   --prompt-template prompts/crash_triage_prompt_template.md \   --prompt-output reports/phase3_triage/open5gs/open5gs_llm_triage_prompt.md 

### Run local LLM triage using Ollama

bash ollama run qwen2.5-coder:7b < reports/phase3_triage/toy_nas_tlv/toy_llm_triage_prompt.md > reports/phase3_triage/toy_nas_tlv/toy_llm_triage_output.md 

bash ollama run qwen2.5-coder:7b < reports/phase3_triage/open5gs/open5gs_llm_triage_prompt.md > reports/phase3_triage/open5gs/open5gs_llm_triage_output.md 

## Final Conclusion

Phase 3 demonstrates that LLMs can support fuzzing-result interpretation when supplied with structured evidence, source-code context, and conservative guardrails. The LLM correctly classified the toy target crash as an intentional validation crash and correctly classified the Open5GS run as a no-crash fuzzing result.

The main conclusion is that LLMs are useful as assistants for source-code-aware triage and report generation, but they should not be treated as autonomous vulnerability classifiers. Human review remains necessary before any security claim is made.
