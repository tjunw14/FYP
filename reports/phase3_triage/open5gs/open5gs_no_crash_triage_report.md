# Phase 3 Crash Triage Report: open5gs_registration_request

## 1. Summary

This report analyses the fuzzing result for `open5gs_registration_request` using available AFL++ evidence, harness code, source-code context, and optional sanitizer output.

The purpose of this report is to classify the observed behaviour carefully without overclaiming vulnerability impact.

## 2. Initial Classification

| Field | Assessment |
|---|---|
| Target | `open5gs_registration_request` |
| Observed crash type | `No crash or hang observed` |
| Vulnerability confirmed? | No |
| Requires manual verification? | Yes |
| Confidence | Depends on source-code evidence |

## 3. AFL++ Evidence

start_time        : 1780657626
last_update       : 1780664824
run_time          : 7197
fuzzer_pid        : 95418
cycles_done       : 10
cycles_wo_finds   : 0
time_wo_finds     : 483
fuzz_time         : 6297
calibration_time  : 15
cmplog_time       : 0
sync_time         : 0
trim_time         : 884
execs_done        : 855466
execs_per_sec     : 118.85
execs_ps_last_min : 103.72
corpus_count      : 454
corpus_favored    : 103
corpus_found      : 434
corpus_imported   : 0
corpus_variable   : 0
max_depth         : 11
cur_item          : 214
pending_favs      : 0
pending_total     : 2
stability         : 100.00%
bitmap_cvg        : 3.01%
saved_crashes     : 0
saved_hangs       : 0
total_tmout       : 279
last_find         : 1780664759
last_crash        : 0
last_hang         : 0
execs_since_crash : 855466
exec_timeout      : 40
slowest_exec_ms   : 0
peak_rss_mb       : 0
cpu_affinity      : 0
edges_found       : 322
total_edges       : 10706
var_byte_count    : 0
havoc_expansion   : 0
auto_dict_entries : 0
testcache_size    : 246213
testcache_count   : 448
testcache_evict   : 0
afl_banner        : ./harness_registration_request
afl_version       : ++4.41a
target_mode       : shmem_testcase default
command_line      : afl-fuzz -i seeds_registration_llm -o out_registration_llm_2h -- ./harness_registration_request @@


## 4. Harness Context

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "core/ogs-core.h"
#include "nas/5gs/ogs-nas-5gs.h"

int ogs_nas_5gs_decode_registration_request(
    ogs_nas_5gs_message_t *message,
    ogs_pkbuf_t *pkbuf
);


/*
 * First Open5GS AFL++ harness.
 *
 * Target:
 *   ogs_nas_5gs_decode_registration_request()
 *
 * Input format:
 *   AFL++ input is treated as the body of a 5G NAS Registration Request.
 *
 * Note:
 *   This is a message-specific decoder harness, not a full NAS dispatcher harness.
 */

int main(int argc, char **argv)
{
    FILE *fp = NULL;
    uint8_t input[4096];
    size_t len = 0;

    ogs_pkbuf_t *pkbuf = NULL;
    ogs_nas_5gs_message_t message;

    if (argc != 2) {
        return 1;
    }

    fp = fopen(argv[1], "rb");
    if (!fp) {
        return 1;
    }

    len = fread(input, 1, sizeof(input), fp);
    fclose(fp);

    if (len == 0) {
        return 0;
    }

    memset(&message, 0, sizeof(message));

    ogs_pkbuf_init();

    pkbuf = ogs_pkbuf_alloc(NULL, (unsigned int)len);
    if (!pkbuf) {
        ogs_pkbuf_final();
        return 0;
    }

    ogs_pkbuf_put_data(pkbuf, input, (unsigned int)len);

    /*
     * We ignore the return value because AFL++ is interested in crashes,
     * sanitizer findings, and abnormal exits.
     */
    (void)ogs_nas_5gs_decode_registration_request(&message, pkbuf);

    ogs_pkbuf_free(pkbuf);
    ogs_pkbuf_final();

    return 0;
}


## 5. Target Source-Code Context

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


## 6. Sanitizer / Runtime Output

Not provided.

## 7. Additional Notes

The Open5GS two-hour LLM-assisted fuzzing run completed with 100% stability and found 0 crashes and 0 hangs. This result should be interpreted as stable fuzzing evidence, not vulnerability discovery.

## 8. Guarded Analysis

Based on the supplied evidence, no crash or hang was observed during this fuzzing run.

This result should not be classified as vulnerability discovery. Instead, it should be interpreted as evidence that the harness and target remained stable during the recorded AFL++ run.

The AFL++ statistics show 0 saved crashes and 0 saved hangs. Therefore, there is no crash artifact to triage and no confirmed vulnerability to report from this run.

## 9. Security Impact

No real security impact should be claimed unless the crash is confirmed to occur in production-relevant code and is supported by source-code evidence, sanitizer evidence, and a reproducible execution path.

At this stage, the finding should be described as a fuzzing-triggered crash, validation event, or no-crash fuzzing result. It should not be described as remote code execution, buffer overflow, integer overflow, or denial of service unless those claims are directly supported by evidence.

## 10. Recommended Next Steps

1. Reproduce any saved crash with the AFL++ input if a crash exists.
2. Capture sanitizer output if available.
3. Identify the exact crashing function and source line if a crash exists.
4. Confirm whether the behaviour exists in real target code or only in a toy/test target.
5. Avoid assigning vulnerability labels until the root cause is verified from source code.
6. If no crash exists, document the run as stable fuzzing evidence rather than vulnerability discovery.

## 11. Final Conclusion

The fuzzing run completed without crashes or hangs. This does not prove that the target is vulnerability-free, but it means the available AFL++ evidence does not support a vulnerability claim.

The result should be reported as stable fuzzing evidence and as a no-crash case for the Phase 3 triage framework.
