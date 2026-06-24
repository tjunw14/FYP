# Phase 4: Protocol-Aware Open5GS Seed Generation and AFL++ Dictionary Support

## Overview

Phase 4 was conducted after the Phase 2 Open5GS fuzzing experiments showed that LLM-assisted seeds were valid and stable, but did not produce a clear coverage advantage over the baseline. The goal of Phase 4 was to improve fuzzing effectiveness by introducing more protocol-aware Open5GS Registration Request seeds and an AFL++ dictionary containing NAS-related byte tokens.

The target remained the Open5GS NAS 5GS Registration Request decoder:

`ogs_nas_5gs_decode_registration_request()`

The same harness, `harness_registration_request`, was used. The harness treats AFL++ input as the body of a Registration Request message.

## Phase 4 Setup

Two additions were made:

1. A protocol-aware seed generator:
   `scripts/generate_open5gs_registration_seeds.py`
2. An AFL++ dictionary:
   `targets/open5gs/nas_registration_request.dict`

The generated protocol-aware seed corpus was saved in:

`targets/open5gs/seeds_registration_protocol/`

The dictionary included byte tokens for common registration types, length markers, padding patterns, mobile identity-like patterns, and selected NAS Information Element markers.

## Important Caveat

Phase 4 was run using AFL++ `++5.02a`, while the earlier Phase 2 30-minute experiments used AFL++ `++4.41a`.

Because of this version difference, comparisons between Phase 2 and Phase 4 should be interpreted as exploratory rather than perfectly controlled. The most direct Phase 4 comparison is between:

1. Protocol-aware seeds without dictionary
2. Protocol-aware seeds with dictionary

Both Phase 4 runs used AFL++ `++5.02a`.

## Phase 4 Experiment 1: Protocol-Aware Seeds Without Dictionary

| Metric | Result |
|---|---:|
| AFL++ version | `++5.02a` |
| Runtime | 1797 seconds |
| Executions | 207,409 |
| Executions/sec | 115.36 |
| Corpus count | 377 |
| Corpus found | 357 |
| Corpus favored | 110 |
| Max depth | 6 |
| Bitmap coverage | 3.00% |
| Edges found | 321 / 10,707 |
| Saved crashes | 0 |
| Saved hangs | 0 |
| Total timeouts | 87 |
| Stability | 100.00% |

The protocol-aware seed run completed successfully with 100% stability. It produced no crashes or hangs. Compared with the earlier Phase 2 baseline, it produced a larger corpus and fewer timeouts, but reached lower maximum depth and did not improve edge coverage.

## Phase 4 Experiment 2: Protocol-Aware Seeds With AFL++ Dictionary

| Metric | Result |
|---|---:|
| AFL++ version | `++5.02a` |
| Runtime | 1797 seconds |
| Executions | 193,281 |
| Executions/sec | 107.50 |
| Corpus count | 354 |
| Corpus found | 334 |
| Corpus favored | 111 |
| Max depth | 5 |
| Bitmap coverage | 3.01% |
| Edges found | 322 / 10,707 |
| Saved crashes | 0 |
| Saved hangs | 0 |
| Total timeouts | 102 |
| Stability | 100.00% |

The dictionary-assisted run also completed successfully with 100% stability and found no crashes or hangs. Compared with the protocol-seed-only Phase 4 run, the dictionary run discovered one additional edge and slightly increased bitmap coverage from 3.00% to 3.01%. However, it executed fewer test cases, produced a smaller corpus, reached a lower maximum depth, and had more timeouts.

## Phase 4 Comparison Table

| Metric | Phase 2 Baseline 30m | Phase 2 LLM-assisted 30m | Phase 4 Protocol Seeds 30m | Phase 4 Protocol Seeds + Dictionary 30m |
|---|---:|---:|---:|---:|
| AFL++ version | `++4.41a` | `++4.41a` | `++5.02a` | `++5.02a` |
| Runtime | 1798 s | 1797 s | 1797 s | 1797 s |
| Executions | 210,442 | 234,895 | 207,409 | 193,281 |
| Executions/sec | 117.00 | 130.65 | 115.36 | 107.50 |
| Corpus count | 348 | 371 | 377 | 354 |
| Corpus found | 345 | 351 | 357 | 334 |
| Corpus favored | 118 | 117 | 110 | 111 |
| Max depth | 8 | 9 | 6 | 5 |
| Bitmap coverage | 3.00% | 2.99% | 3.00% | 3.01% |
| Edges found | 321 / 10,706 | 320 / 10,706 | 321 / 10,707 | 322 / 10,707 |
| Saved crashes | 0 | 0 | 0 | 0 |
| Saved hangs | 0 | 0 | 0 | 0 |
| Total timeouts | 312 | 133 | 87 | 102 |
| Stability | 100.00% | 100.00% | 100.00% | 100.00% |

## Interpretation

The protocol-aware seed corpus improved some secondary metrics compared with the original 30-minute baseline, especially corpus count and timeout reduction. However, it did not improve edge coverage over the baseline and reached a lower maximum depth.

The AFL++ dictionary produced the clearest coverage-related change within Phase 4. The dictionary run discovered 322 edges compared with 321 edges in the protocol-seed-only run, and bitmap coverage increased from 3.00% to 3.01%. This suggests that dictionary support can help AFL++ reach at least one additional parser path in the Open5GS Registration Request decoder.

However, the dictionary run also reduced throughput and corpus growth. It executed 14,128 fewer test cases than the protocol-seed-only run, produced 23 fewer corpus entries, reached a lower maximum depth, and had 15 more timeouts.

Therefore, the Phase 4 result is mixed. Dictionary support gave a small edge and coverage improvement, but did not clearly improve overall fuzzing efficiency in the 30-minute run.

## Security Result

No Phase 4 run discovered crashes or hangs.

This means Phase 4 does not demonstrate vulnerability discovery. The correct interpretation is that protocol-aware seed generation and dictionary support were successfully integrated into the AFL++ Open5GS fuzzing workflow, and dictionary support produced a small coverage/edge improvement, but no crash evidence was produced.

## Report-Ready Conclusion

Phase 4 explored whether protocol-aware seed generation and AFL++ dictionary support could improve fuzzing effectiveness for the Open5GS NAS 5GS Registration Request decoder. A new protocol-aware seed corpus and NAS-focused AFL++ dictionary were created and tested in two 30-minute fuzzing runs.

The protocol-aware seed run executed 207,409 test cases, achieved 3.00% bitmap coverage, discovered 321 edges, and found no crashes or hangs. The dictionary-assisted run executed 193,281 test cases, achieved 3.01% bitmap coverage, discovered 322 edges, and also found no crashes or hangs.

Compared with the protocol-seed-only run, the dictionary-assisted run discovered one additional edge and slightly improved bitmap coverage. However, it had lower throughput, a smaller final corpus, lower maximum depth, and more timeouts. Therefore, the dictionary provided a small coverage benefit but did not clearly improve overall fuzzing efficiency within the 30-minute experiment.

Overall, Phase 4 shows that protocol-aware seed generation and dictionary support can be integrated into the Open5GS AFL++ fuzzing workflow. The results suggest a small benefit from dictionary-guided mutation, but further work is needed to improve seed quality, message modelling, and target coverage. No vulnerabilities were discovered in this phase.
