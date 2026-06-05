# Phase 2D: Open5GS Baseline vs LLM-Assisted Seed Fuzzing Summary

## Experiment Overview

After validating the AFL++ and LLM-assisted fuzzing pipeline on a toy NAS-like TLV parser, the project moved to a real open-source 5G software target using Open5GS. The selected fuzzing target was the Open5GS NAS 5GS Registration Request decoder function:

`ogs_nas_5gs_decode_registration_request()`

A custom AFL++ harness, `harness_registration_request`, was created to read AFL++ input bytes, wrap them in an Open5GS `ogs_pkbuf_t` packet buffer, initialise an `ogs_nas_5gs_message_t` structure, and pass the input to the registration request decoder.

Two 30-minute fuzzing experiments were conducted:

1. Baseline AFL++ fuzzing using manual/basic seeds.
2. LLM-assisted AFL++ fuzzing using an LLM-assisted Open5GS NAS registration request seed corpus.

## Baseline Result

The baseline run executed 210,442 test cases over 1798 seconds at 117.00 executions per second. AFL++ expanded the corpus to 348 entries and discovered 345 corpus items. The run achieved 3.00% bitmap coverage, corresponding to 321 discovered edges out of 10,706 total edges. No crashes or hangs were observed, and stability remained at 100%.

## LLM-Assisted Result

The LLM-assisted run executed 234,895 test cases over 1797 seconds at 130.65 executions per second. AFL++ expanded the corpus to 371 entries and discovered 351 corpus items. The run achieved 2.99% bitmap coverage, corresponding to 320 discovered edges out of 10,706 total edges. No crashes or hangs were observed, and stability remained at 100%.

## Comparison

Compared with the baseline run, the LLM-assisted run executed 24,453 more test cases within a similar runtime, representing an execution increase of approximately 11.62%. It also produced 23 more corpus entries, discovered 6 more corpus items, reached a slightly higher maximum depth of 9 compared with 8, and reduced the number of timeouts from 312 to 133.

However, bitmap coverage and edge coverage remained almost unchanged. The baseline run achieved 3.00% bitmap coverage and found 321 edges, while the LLM-assisted run achieved 2.99% bitmap coverage and found 320 edges. Neither run discovered crashes or hangs.

## Interpretation

The Open5GS results show that the AFL++ harness is stable and capable of fuzzing real NAS 5G parser code. The LLM-assisted seed corpus improved execution throughput, corpus size, and timeout behaviour, but did not produce a meaningful coverage improvement or discover vulnerabilities in this experiment.

This result should not be interpreted as vulnerability discovery. Instead, it supports the claim that LLM-assisted seed generation can produce valid AFL++ inputs for real open-source 5G software and may improve corpus growth and fuzzing throughput. Further work is needed to improve protocol awareness, increase coverage, run longer experiments, and add source-code-aware LLM crash analysis if sanitizer crashes are discovered.

## Report-Ready Conclusion

A 30-minute baseline AFL++ fuzzing run and a 30-minute LLM-assisted seed fuzzing run were conducted against the Open5GS NAS 5GS Registration Request decoder. The baseline run executed 210,442 test cases, achieved 3.00% bitmap coverage, discovered 321 edges, and produced no crashes or hangs. The LLM-assisted run executed 234,895 test cases, achieved 2.99% bitmap coverage, discovered 320 edges, and also produced no crashes or hangs.

Compared with the baseline, the LLM-assisted run executed 24,453 more test cases and produced 23 more corpus entries within a similar runtime. It also reduced the number of timeouts from 312 to 133. However, coverage remained nearly unchanged and no vulnerabilities were discovered. These results suggest that LLM-assisted seed generation can support AFL++ fuzzing of Open5GS by producing valid parser inputs and improving corpus growth, but further work is needed to improve coverage and perform deeper vulnerability analysis.
