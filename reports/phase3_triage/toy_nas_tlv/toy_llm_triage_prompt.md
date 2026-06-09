# LLM-Assisted Crash Triage Prompt

You are assisting with defensive fuzzing and vulnerability analysis.

Your task is to analyse AFL++ fuzzing evidence conservatively. Do not overclaim. Do not label a finding as buffer overflow, integer overflow, denial of service, remote code execution, or real vulnerability unless the supplied evidence directly supports it.

## Required Rules

1. Use only the supplied evidence.
2. If source code shows an intentional abort, classify it as an intentional validation crash, not a real vulnerability.
3. If AFL++ found 0 crashes and 0 hangs, classify it as a no-crash fuzzing result, not vulnerability discovery.
4. If sanitizer output is missing, state that sanitizer evidence is unavailable.
5. Always include confidence level and limitations.
6. Always separate confirmed facts from hypotheses.

## Target

toy_nas_tlv

## Observed Crash Type

SIGABRT from intentional abort condition

## AFL++ Evidence

start_time        : 1780467892
last_update       : 1780468677
run_time          : 784
fuzzer_pid        : 21
cycles_done       : 11
cycles_wo_finds   : 0
time_wo_finds     : 241
fuzz_time         : 775
calibration_time  : 1
cmplog_time       : 0
sync_time         : 0
trim_time         : 7
execs_done        : 106106
execs_per_sec     : 135.20
execs_ps_last_min : 125.88
corpus_count      : 53
corpus_favored    : 14
corpus_found      : 48
corpus_imported   : 0
corpus_variable   : 0
max_depth         : 7
cur_item          : 39
pending_favs      : 0
pending_total     : 3
stability         : 100.00%
bitmap_cvg        : 33.33%
saved_crashes     : 1
saved_hangs       : 0
total_tmout       : 13
last_find         : 1780468630
last_crash        : 1780468202
last_hang         : 0
execs_since_crash : 62149
exec_timeout      : 40
slowest_exec_ms   : 0
peak_rss_mb       : 0
cpu_affinity      : 0
edges_found       : 24
total_edges       : 72
var_byte_count    : 0
havoc_expansion   : 5
auto_dict_entries : 0
testcache_size    : 6709
testcache_count   : 53
testcache_evict   : 0
afl_banner        : ./toy_nas_tlv
afl_version       : ++4.41a
target_mode       : shmem_testcase default
command_line      : afl-fuzz -i seeds_llm -o out_llm -- ./toy_nas_tlv @@


## Harness Code

Not provided.

## Source-Code Context

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static int parse_tlv_payload(const uint8_t *data, size_t len) {
    size_t offset = 0;
    int score = 0;

    while (offset + 2 <= len) {
        uint8_t tag = data[offset++];
        uint8_t field_len = data[offset++];

        if (offset + field_len > len) {
            return -1;
        }

        const uint8_t *value = data + offset;

        switch (tag) {
        case 0x01:
            if (field_len == 1 && value[0] == 0x7f) {
                score += 3;
            }
            break;
        case 0x02:
            if (field_len >= 2 && value[0] == 0x13 && value[1] == 0x37) {
                score += 5;
            }
            break;
        case 0x7e:
            if (field_len >= 4 && value[0] == 'N' && value[1] == 'A' && value[2] == 'S') {
                score += 7;
            }
            break;
        default:
            score += tag & 1;
            break;
        }

        offset += field_len;
    }

    return score;
}

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size < 2) {
        return 0;
    }

    uint8_t message_type = data[0];
    uint8_t payload_len = data[1];

    if ((size_t)payload_len > size - 2) {
        return 0;
    }

    const uint8_t *payload = data + 2;
    int score = parse_tlv_payload(payload, payload_len);

    if (message_type == 0x41 && payload_len >= 4 && score > 10) {
        /* Deliberate educational crash for AFL++ pipeline validation only. */
        abort();
    }

    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: %s <input>\n", argv[0]);
        return 1;
    }

    FILE *fp = fopen(argv[1], "rb");
    if (!fp) {
        perror("fopen");
        return 1;
    }

    uint8_t buf[4096];
    size_t n = fread(buf, 1, sizeof(buf), fp);
    fclose(fp);

    LLVMFuzzerTestOneInput(buf, n);
    return 0;
}


## Sanitizer / Runtime Output

Not provided.

## Additional Notes

This toy target contains an intentional abort condition. The crash is used to validate the AFL++ and LLM-assisted triage pipeline. It must not be reported as a real vulnerability.

## Output Format

Please produce a Markdown report with these sections:

1. Summary
2. Confirmed Evidence
3. Crash or No-Crash Classification
4. Likely Root Cause
5. Security Impact
6. Confidence Level
7. Limitations
8. Manual Verification Steps
9. Final Conservative Conclusion
