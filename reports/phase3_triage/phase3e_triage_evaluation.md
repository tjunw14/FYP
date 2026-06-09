# Phase 3E: Evaluation of LLM-Assisted Triage Outputs

## Overview

Phase 3 evaluates the vulnerability analysis component of the project. After generating guarded triage reports and LLM-ready prompts, the prompts were passed to the local LLM model `qwen2.5-coder:7b` through Ollama. The resulting LLM outputs were compared against the known ground truth and the guarded report outputs.

Two cases were evaluated:

1. `toy_nas_tlv`, where AFL++ found a known intentional SIGABRT crash.
2. `open5gs_registration_request`, where AFL++ found no crashes or hangs during the two-hour LLM-assisted fuzzing run.

The goal was to determine whether the LLM can assist fuzzing-result triage without overclaiming vulnerability impact.

## Case 1: Toy NAS-like TLV Target

The toy target contains a deliberate educational crash condition using `abort()`. Therefore, the correct classification is an intentional validation crash, not a real vulnerability.

The LLM output correctly classified the crash as an intentional validation crash. It identified the relevant source-code condition and avoided unsupported claims such as buffer overflow, integer overflow, remote code execution, or confirmed denial-of-service vulnerability.

| Criterion | Result |
|---|---|
| Correctly identified crash type | Yes |
| Used source-code evidence | Yes |
| Avoided vulnerability overclaiming | Yes |
| Correctly stated no real security impact | Yes |
| Mentioned sanitizer limitation | Yes |
| Overall assessment | Successful |

This shows that, when given source-code context and explicit guardrails, the LLM can correctly distinguish a controlled validation crash from a real vulnerability.

## Case 2: Open5GS Registration Request Decoder

The Open5GS two-hour LLM-assisted fuzzing run completed with 0 saved crashes, 0 saved hangs, 3.01% bitmap coverage, 322 discovered edges, and 100.00% stability.

Therefore, the correct classification is a no-crash fuzzing result, not vulnerability discovery.

The LLM correctly classified the Open5GS result as a no-crash outcome. It avoided claiming vulnerability discovery and included limitations such as limited fuzzing time, missing sanitizer output, and the fact that fuzzing one function does not prove the entire target is free of vulnerabilities.

However, one phrase was slightly too strong: “the function is functioning correctly with the provided seeds.” A safer wording would be: “the available fuzzing evidence did not trigger crashes or hangs with the provided seeds.”

| Criterion | Result |
|---|---|
| Correctly identified no-crash case | Yes |
| Avoided vulnerability discovery claim | Yes |
| Mentioned limitations | Yes |
| Avoided major overclaiming | Yes |
| Used slightly overconfident wording | Yes |
| Human review still required | Yes |
| Overall assessment | Mostly successful |

## Comparison Between Guarded Report and LLM Output

| Aspect | Guarded Script Output | LLM Output |
|---|---|---|
| Consistency | Highly consistent | Mostly consistent |
| Flexibility | Template-based | More explanatory |
| Overclaiming risk | Low | Low to moderate |
| Source-code reasoning | Limited to supplied context | Better natural-language explanation |
| Need for review | Low | Still required |
| Best use | Baseline safe report | Human-reviewed analysis draft |

The guarded script output is safer and more consistent, while the LLM output is more descriptive and easier to read. The best workflow is to use both together: the guarded script provides a conservative baseline, and the LLM output provides a more detailed explanation that must be reviewed before inclusion in the report.

## Key Learning

The Phase 3 results support one of the main lessons from the project: LLM-assisted vulnerability analysis requires source-code context and strict guardrails.

Without context, an LLM may overclaim a fuzzing crash as a buffer overflow, integer overflow, remote code execution, or denial of service. With source-code evidence and explicit instructions, the LLM correctly classified the toy crash as an intentional validation crash and correctly classified the Open5GS run as a no-crash fuzzing result.

However, the Open5GS output also shows that LLM-generated reports should not be accepted automatically. Even when no major overclaiming occurs, the wording may still be slightly too confident and should be reviewed by a human.

## Report-Ready Conclusion

Phase 3 demonstrates that LLMs can assist with fuzzing result interpretation when provided with structured evidence, source-code context, and conservative guardrails. For the toy NAS-like TLV target, the LLM correctly classified the AFL++ crash as an intentional validation crash caused by a deliberate `abort()` condition, rather than a real vulnerability. For the Open5GS NAS Registration Request decoder, the LLM correctly classified the two-hour fuzzing run as a no-crash result and avoided claiming vulnerability discovery.

These results show that LLM-assisted triage can support fuzzing workflows by helping explain crash and no-crash outcomes. However, the outputs still require human review, especially to avoid overly confident wording. Therefore, the role of the LLM in this project is best framed as an assistant for source-code-aware triage and report generation, not as an autonomous vulnerability classifier.
