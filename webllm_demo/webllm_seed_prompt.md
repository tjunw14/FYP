# WebLLM Seed Generation Prompt

Use this prompt in the WebLLM browser demo to generate seed inputs for the Open5GS NAS 5G Registration Request AFL++ harness.

```text
You are assisting a defensive fuzzing experiment for an open-source 5G network software parser.

Target:
- Open5GS NAS 5G Registration Request decoder
- Function: ogs_nas_5gs_decode_registration_request()
- AFL++ harness input is treated as the body of a Registration Request message, not a full NAS packet.

Task:
Generate 20 small binary seed inputs as hexadecimal strings for AFL++.

Seed design goals:
- Keep each seed between 4 and 64 bytes.
- Include variation in registration type-like first bytes.
- Include short, malformed, truncated, padded, and length-mismatch cases.
- Include mobile-identity-like byte patterns.
- Include NAS information-element-like tags such as 2e, 2f, 52, 17, 40, 50, 25, 2b, 77, 18, 51, 70, 74, and 7b.
- These are defensive fuzzing seeds only. Do not include exploit instructions.

Output format rules:
- Output only seed lines.
- Do not include explanations.
- Use this exact format:

seed_001: <hex bytes>
seed_002: <hex bytes>
...
seed_020: <hex bytes>

Example format:
seed_001: 4101f0
seed_002: 7e0041012e00
```
