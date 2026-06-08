# Phase 2F: Open5GS Two-Hour Baseline vs LLM-Assisted Comparison

## Experiment Overview

After completing the initial 30-minute Open5GS fuzzing comparison, a longer two-hour experiment was conducted to evaluate whether the earlier trends remained consistent over a longer runtime. The target remained the Open5GS NAS 5GS Registration Request decoder:

`ogs_nas_5gs_decode_registration_request()`

The same AFL++ harness, `harness_registration_request`, was used for both runs. The harness reads AFL++ input bytes, wraps them in an Open5GS `ogs_pkbuf_t` packet buffer, initialises an `ogs_nas_5gs_message_t` structure, and passes the input to the Open5GS registration request decoder.

Two experiments were conducted:

1. A two-hour baseline run using manual/basic seed inputs.
2. A two-hour LLM-assisted run using the LLM-assisted Open5GS NAS registration request seed corpus.

The purpose of this experiment was not to claim vulnerability discovery, but to compare fuzzing behaviour over a longer period using baseline seeds versus LLM-assisted seeds.

## Baseline Two-Hour Run

| Metric | Baseline 2h Result |
|---|---:|
| Target software | Open5GS |
| Target function | `ogs_nas_5gs_decode_registration_request()` |
| Harness | `harness_registration_request` |
| Seed type | Manual/basic seeds |
| AFL++ version | `++4.41a` |
| Runtime | 7198 seconds |
| Executions | 892,769 |
| Executions/sec | 124.02 |
| Corpus count | 448 |
| Corpus found | 445 |
| Corpus favored | 109 |
| Max depth | 10 |
| Bitmap coverage | 3.01% |
| Edges found | 322 / 10,706 |
| Saved crashes | 0 |
| Saved hangs | 0 |
| Total timeouts | 181 |
| Stability | 100.00% |

The two-hour baseline run completed successfully with 100% stability. AFL++ executed 892,769 test cases and expanded the corpus to 448 entries. The run achieved 3.01% bitmap coverage and discovered 322 edges out of 10,706 total edges. No crashes or hangs were found.

## LLM-Assisted Two-Hour Run

| Metric | LLM-Assisted 2h Result |
|---|---:|
| Target software | Open5GS |
| Target function | `ogs_nas_5gs_decode_registration_request()` |
| Harness | `harness_registration_request` |
| Seed type | LLM-assisted seeds |
| AFL++ version | `++4.41a` |
| Runtime | 7197 seconds |
| Executions | 855,466 |
| Executions/sec | 118.85 |
| Corpus count | 454 |
| Corpus found | 434 |
| Corpus favored | 103 |
| Max depth | 11 |
| Bitmap coverage | 3.01% |
| Edges found | 322 / 10,706 |
| Saved crashes | 0 |
| Saved hangs | 0 |
| Total timeouts | 279 |
| Stability | 100.00% |

The two-hour LLM-assisted run also completed successfully with 100% stability. AFL++ executed 855,466 test cases and expanded the corpus to 454 entries. The run achieved the same 3.01% bitmap coverage and discovered the same number of edges as the baseline run, with 322 out of 10,706 edges discovered. No crashes or hangs were found.

## Two-Hour Baseline vs LLM-Assisted Comparison

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

## Derived Metrics

| Derived Metric | Result |
|---|---:|
| Runtime difference | LLM-assisted run was 1 second shorter |
| Execution difference | LLM-assisted run executed 37,303 fewer test cases |
| Execution change | LLM-assisted run executed approximately 4.18% fewer test cases |
| Execution speed difference | LLM-assisted run was 5.17 exec/sec slower |
| Corpus count difference | LLM-assisted run produced 6 more corpus entries |
| Corpus found difference | LLM-assisted run found 11 fewer corpus items |
| Max depth difference | LLM-assisted run reached depth 11 vs baseline depth 10 |
| Coverage difference | No difference; both achieved 3.01% bitmap coverage |
| Edge difference | No difference; both discovered 322 edges |
| Timeout difference | LLM-assisted run had 98 more timeouts |
| Crash difference | No difference; both found 0 crashes |
| Hang difference | No difference; both found 0 hangs |
| Stability difference | No difference; both maintained 100.00% stability |

## Interpretation

The two-hour experiment provides a more stable and longer-duration comparison between baseline AFL++ fuzzing and LLM-assisted seed fuzzing on the Open5GS NAS 5GS Registration Request decoder.

Unlike the earlier 30-minute experiment, where the LLM-assisted run achieved higher execution throughput and fewer timeouts, the two-hour experiment produced a more balanced result. In the two-hour run, the baseline achieved higher execution throughput and fewer timeouts, while the LLM-assisted run produced a slightly larger final corpus and reached a slightly greater maximum depth.

Both runs achieved the same bitmap coverage of 3.01% and discovered the same number of edges, 322 out of 10,706. Neither run discovered crashes or hangs, and both maintained 100% stability throughout the experiment.

This suggests that the LLM-assisted seed corpus remained valid and stable for longer fuzzing, but it did not produce a clear coverage advantage over the baseline in this experiment. The LLM-assisted run may have encouraged slightly deeper exploration, as shown by the higher max depth, but this did not translate into additional edge coverage or crash discovery.

## Report-Ready Conclusion

A two-hour baseline AFL++ fuzzing run and a two-hour LLM-assisted seed fuzzing run were conducted against the Open5GS NAS 5GS Registration Request decoder. The baseline run executed 892,769 test cases, achieved 3.01% bitmap coverage, discovered 322 edges, and produced no crashes or hangs. The LLM-assisted run executed 855,466 test cases, achieved the same 3.01% bitmap coverage, discovered the same 322 edges, and also produced no crashes or hangs.

Compared with the baseline, the LLM-assisted run produced a slightly larger final corpus and reached a greater maximum depth. However, it executed fewer test cases, had more timeouts, and did not improve edge coverage. Both runs remained stable at 100% and did not reveal any crashes or hangs.

Therefore, the two-hour Open5GS experiment does not show vulnerability discovery or a clear coverage advantage from LLM-assisted seeds. Instead, it demonstrates that LLM-assisted seed generation can produce valid AFL++ inputs for real Open5GS NAS parser fuzzing and can support stable long-duration fuzzing. Further improvements are needed, such as more protocol-aware seed generation, better NAS message modelling, dictionary support, and source-code-aware crash analysis if sanitizer findings are discovered in future experiments.
