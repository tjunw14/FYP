# Phase 5: WebLLM-Driven AFL++ Seed Generation Demo

## Purpose

This phase demonstrates a WebLLM-driven seed generation workflow for the existing Open5GS AFL++ fuzzing pipeline. WebLLM was used as a browser-based local small language model component to generate hexadecimal seed inputs for AFL++.

The goal was not to outperform earlier fuzzing experiments, but to demonstrate that a browser/local LLM can be integrated into the fuzzing workflow as a low-cost edge-device-oriented seed generation component.

## Workflow

1. A WebLLM browser demo was used to generate hexadecimal AFL++ seed inputs.
2. The generated seed lines were saved as `webllm_generated_seeds.txt`.
3. The seed lines were converted into binary AFL++ `.bin` files using `scripts/import_webllm_hex_seeds.py`.
4. The binary seeds were used as the input corpus for the existing Open5GS Registration Request AFL++ harness.
5. AFL++ fuzzing results were collected from `fuzzer_stats`.

## Target

- Software: Open5GS
- Target function: `ogs_nas_5gs_decode_registration_request()`
- Harness: `targets/open5gs/harness_registration_request.c`
- Input interpretation: AFL++ input is treated as the body of a NAS 5G Registration Request message.

## WebLLM Seed Corpus

The WebLLM-generated corpus contained 10 seed files. The seeds were small hexadecimal inputs containing registration-type-like bytes, malformed/truncated structures, mobile-identity-like byte patterns, and NAS information-element-like byte tags.

## AFL++ Results

| Metric | Result |
|---|---:|
| AFL++ version | `++5.02a` |
| Runtime | 898 seconds |
| Executions | 113,325 |
| Executions/sec | 126.13 |
| Corpus count | 284 |
| Corpus found | 272 |
| Corpus favored | 112 |
| Max depth | 4 |
| Bitmap coverage | 2.99% |
| Edges found | 320 / 10,707 |
| Saved crashes | 0 |
| Saved hangs | 0 |
| Total timeouts | 14 |
| Stability | 100.00% |

## Interpretation

The WebLLM-generated seeds were accepted by AFL++ and successfully exercised the Open5GS Registration Request harness. The run completed with 100.00% stability and no crashes or hangs.

Compared with the earlier longer experiments, this WebLLM run was shorter and should not be treated as a direct performance comparison. Its main purpose is to demonstrate that browser-based local small language models can be used as a seed-generation component in an AFL++ fuzzing workflow.

## Security Result

No crashes or hangs were discovered. This phase does not demonstrate vulnerability discovery. Instead, it demonstrates successful integration of WebLLM-generated seeds into the existing Open5GS AFL++ fuzzing pipeline.

## Report-Ready Conclusion

A WebLLM-driven seed generation demo was added to explore how local small language models could support fuzzing workflows in low-cost or edge-device settings. The browser-based WebLLM component generated seed inputs, which were converted into AFL++ binary seed files and used to fuzz the Open5GS NAS 5G Registration Request decoder. The 15-minute AFL++ run completed successfully with 113,325 executions, 2.99% bitmap coverage, 320 discovered edges, and no crashes or hangs. This demonstrates that WebLLM can be integrated as a local LLM seed-generation component in the project workflow.
