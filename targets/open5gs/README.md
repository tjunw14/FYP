# Open5GS Target Notes

Open5GS is the recommended main 5G target for this FYP.

## Why Open5GS?

- open-source 5G Core and EPC implementation
- written mostly in C
- realistic telecom/security relevance
- contains protocol parsing code suitable for fuzzing
- can be built in Linux/WSL2/Docker

## Initial fuzzing area

Start with 5G NAS message parsing/decoding, especially files under Open5GS paths such as:

```text
lib/nas/5gs/
```

The first research harness should aim to call the NAS 5GS decoder with AFL++ input bytes.

## Phased plan

### Phase 1: Toy parser

Use `targets/toy_nas_tlv` to prove that the AFL++ and LLM pipeline works.

### Phase 2: Open5GS build

Clone Open5GS inside the WSL2/Docker fuzzing environment and confirm a normal source build.

### Phase 3: Harness discovery

Identify the smallest stable decoder function that accepts byte buffers and returns parse results.

### Phase 4: AFL++ harness

Create a C harness that:

1. reads bytes from AFL++,
2. passes them to the Open5GS decoder,
3. exits cleanly on normal parser rejection,
4. lets sanitizer/AFL++ detect memory safety issues.

### Phase 5: Evaluation

Compare:

- baseline manual seeds
- LLM-generated protocol-aware seeds
- coverage growth
- crash/hang count
- unique crash signatures
- crash report quality

## Important safety boundary

This project is for defensive testing and vulnerability analysis. Reports should explain likely causes and fixes, not exploit instructions.
