# WebLLM Seed Generation Prompt

Use this prompt in the WebLLM browser workbench to generate seed inputs for the Open5GS NAS 5G Registration Request AFL++ harness.

```text
You are assisting a defensive fuzzing experiment for an open-source 5G network software parser.

Target:
- Open5GS NAS 5G Registration Request decoder
- Function: ogs_nas_5gs_decode_registration_request()
- AFL++ receives the BODY of a 5G Registration Request, not a complete NAS packet.
- Do NOT prepend a full NAS header, extended protocol discriminator, security header, or Registration Request message-type header.

Input interpretation:
- The first body byte should vary values that exercise the registration-type / ngKSI decoding path.
- The decoder then expects a 5GS mobile-identity field with length-related structure.
- Remaining bytes may be interpreted as optional Information Elements.

Task:
Generate EXACTLY 10 UNIQUE binary seed inputs for the initial AFL++ corpus.

Seed requirements:
- Every seed must be between 4 and 32 bytes inclusive.
- Every seed must contain an even number of hexadecimal characters.
- Use only hexadecimal characters 0-9 and a-f.
- Do not use 0x prefixes, spaces, commas, brackets, comments, or English words inside a seed.
- Keep the seeds small and structured rather than producing long random byte strings.
- Do not make all seeds minor variations of one another.

Create a deliberately mixed corpus:
- 3 near-valid Registration Request body seeds with plausible first-byte and mobile-identity-like structure.
- 2 short or truncated seeds that stop at different parsing stages.
- 2 length-mismatch seeds where a length-like byte is intentionally inconsistent with the available following bytes.
- 2 seeds with optional-IE-like trailing data. You may use tags such as 2e, 2f, 52, 17, 40, 50, 25, 2b, 77, 18, 51, 70, 74, or 7b.
- 1 padded or boundary-style seed.

Diversity goals:
- Vary the first body byte across the 10 seeds.
- Vary mobile-identity-like lengths and byte patterns.
- Include both structured and malformed inputs so AFL++ starts from multiple parser states.
- Avoid duplicate seeds.
- Avoid excessive all-zero padding except in the single padded/boundary seed.

Safety:
- These are defensive fuzzing seeds only.
- Do not provide exploit instructions or vulnerability claims.

OUTPUT RULES — FOLLOW EXACTLY:
- Output exactly 10 lines and nothing else.
- Use labels seed_001 through seed_010 in order.
- One seed per line.
- No explanation before or after the seed lines.
- Use this exact format:

seed_001: 4101f000
seed_002: 0203010203
...
seed_010: 7f0477010203

Before answering, silently verify that there are exactly 10 unique lines and that every hexadecimal payload is 4-32 bytes long.
```
