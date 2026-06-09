from pathlib import Path
import argparse


def read_text_file(path: str | None, max_chars: int = 12000) -> str:
    if not path:
        return "Not provided."

    file_path = Path(path)
    if not file_path.exists():
        return f"File not found: {path}"

    data = file_path.read_text(errors="replace")
    if len(data) > max_chars:
        return data[:max_chars] + "\n\n[TRUNCATED]"
    return data


def build_guarded_triage_report(
    target_name: str,
    crash_type: str,
    fuzzer_stats: str,
    harness_code: str,
    source_context: str,
    sanitizer_output: str,
    notes: str,
) -> str:
    return f"""# Phase 3 Crash Triage Report: {target_name}

## 1. Summary

This report analyses the fuzzing result for `{target_name}` using available AFL++ evidence, harness code, source-code context, and optional sanitizer output.

The purpose of this report is to classify the observed behaviour carefully without overclaiming vulnerability impact.

## 2. Initial Classification

| Field | Assessment |
|---|---|
| Target | `{target_name}` |
| Observed crash type | `{crash_type}` |
| Vulnerability confirmed? | No |
| Requires manual verification? | Yes |
| Confidence | Depends on source-code evidence |

## 3. AFL++ Evidence

{fuzzer_stats}

## 4. Harness Context

{harness_code}

## 5. Target Source-Code Context

{source_context}

## 6. Sanitizer / Runtime Output

{sanitizer_output}

## 7. Additional Notes

{notes}

## 8. Guarded Analysis

Based on the supplied evidence, this crash should not automatically be classified as a real vulnerability.

A crash found by AFL++ may indicate a real memory safety issue, but it may also be caused by an intentional assertion, an intentional abort condition, invalid test harness assumptions, expected parser rejection, or incomplete runtime context.

For this target, the most important evidence is the target source code. If the crash path is caused by an intentional `abort()` or assertion inserted for testing purposes, then the result should be treated as a controlled validation event rather than a real vulnerability.

## 9. Security Impact

No real security impact should be claimed unless the crash is confirmed to occur in production-relevant code and is supported by source-code evidence, sanitizer evidence, and a reproducible execution path.

At this stage, the finding should be described as a fuzzing-triggered crash or validation event, not as remote code execution, buffer overflow, integer overflow, or denial of service unless those claims are directly supported by evidence.

## 10. Recommended Next Steps

1. Reproduce the crash with the saved AFL++ input.
2. Capture sanitizer output if available.
3. Identify the exact crashing function and source line.
4. Confirm whether the crash path exists in real target code or only in a toy/test target.
5. Avoid assigning vulnerability labels until the root cause is verified from source code.
6. If the crash is intentional, document it as pipeline validation rather than vulnerability discovery.

## 11. Final Conclusion

The result should be interpreted conservatively. The available evidence is useful for validating the fuzzing and triage pipeline, but it should not be presented as confirmed vulnerability discovery unless supported by stronger source-code and sanitizer evidence.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate guarded AFL++ crash triage report.")
    parser.add_argument("--target-name", required=True)
    parser.add_argument("--crash-type", default="Unknown")
    parser.add_argument("--fuzzer-stats")
    parser.add_argument("--harness-code")
    parser.add_argument("--source-context")
    parser.add_argument("--sanitizer-output")
    parser.add_argument("--notes", default="")
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    report = build_guarded_triage_report(
        target_name=args.target_name,
        crash_type=args.crash_type,
        fuzzer_stats=read_text_file(args.fuzzer_stats),
        harness_code=read_text_file(args.harness_code),
        source_context=read_text_file(args.source_context),
        sanitizer_output=read_text_file(args.sanitizer_output),
        notes=args.notes or "Not provided.",
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report)

    print(f"Generated triage report: {output_path}")


if __name__ == "__main__":
    main()
