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


def load_prompt_template(template_path: str | None) -> str:
    if not template_path:
        return ""

    file_path = Path(template_path)
    if not file_path.exists():
        return ""

    return file_path.read_text(errors="replace")


def build_llm_prompt(
    template: str,
    target_name: str,
    crash_type: str,
    fuzzer_stats: str,
    harness_code: str,
    source_context: str,
    sanitizer_output: str,
    notes: str,
) -> str:
    if not template:
        template = """# LLM-Assisted Crash Triage Prompt

Analyse the supplied AFL++ fuzzing evidence conservatively. Do not overclaim vulnerability impact.

Target: {target_name}
Observed crash type: {crash_type}

AFL++ Evidence:
{fuzzer_stats}

Harness Code:
{harness_code}

Source-Code Context:
{source_context}

Sanitizer / Runtime Output:
{sanitizer_output}

Additional Notes:
{notes}
"""

    return template.format(
        target_name=target_name,
        crash_type=crash_type,
        fuzzer_stats=fuzzer_stats,
        harness_code=harness_code,
        source_context=source_context,
        sanitizer_output=sanitizer_output,
        notes=notes,
    )


def build_guarded_triage_report(
    target_name: str,
    crash_type: str,
    fuzzer_stats: str,
    harness_code: str,
    source_context: str,
    sanitizer_output: str,
    notes: str,
) -> str:
    is_no_crash = "no crash" in crash_type.lower() or "no crash" in notes.lower()

    if is_no_crash:
        guarded_analysis = (
            "Based on the supplied evidence, no crash or hang was observed during this fuzzing run.\n\n"
            "This result should not be classified as vulnerability discovery. Instead, it should be interpreted "
            "as evidence that the harness and target remained stable during the recorded AFL++ run.\n\n"
            "The AFL++ statistics show 0 saved crashes and 0 saved hangs. Therefore, there is no crash artifact "
            "to triage and no confirmed vulnerability to report from this run."
        )

        final_conclusion = (
            "The fuzzing run completed without crashes or hangs. This does not prove that the target is "
            "vulnerability-free, but it means the available AFL++ evidence does not support a vulnerability claim.\n\n"
            "The result should be reported as stable fuzzing evidence and as a no-crash case for the Phase 3 "
            "triage framework."
        )
    else:
        guarded_analysis = (
            "Based on the supplied evidence, this crash should not automatically be classified as a real vulnerability.\n\n"
            "A crash found by AFL++ may indicate a real memory safety issue, but it may also be caused by an "
            "intentional assertion, an intentional abort condition, invalid test harness assumptions, expected "
            "parser rejection, or incomplete runtime context.\n\n"
            "For this target, the most important evidence is the target source code. If the crash path is caused "
            "by an intentional abort() or assertion inserted for testing purposes, then the result should be treated "
            "as a controlled validation event rather than a real vulnerability."
        )

        final_conclusion = (
            "The result should be interpreted conservatively. The available evidence is useful for validating the "
            "fuzzing and triage pipeline, but it should not be presented as confirmed vulnerability discovery unless "
            "supported by stronger source-code and sanitizer evidence."
        )

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

{guarded_analysis}

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

{final_conclusion}
"""


def write_output(path: str | None, content: str) -> None:
    if not path:
        return

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)
    print(f"Generated: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate guarded AFL++ crash triage report and LLM prompt.")
    parser.add_argument("--target-name", required=True)
    parser.add_argument("--crash-type", default="Unknown")
    parser.add_argument("--fuzzer-stats")
    parser.add_argument("--harness-code")
    parser.add_argument("--source-context")
    parser.add_argument("--sanitizer-output")
    parser.add_argument("--notes", default="")
    parser.add_argument("--output", required=True)
    parser.add_argument("--prompt-template")
    parser.add_argument("--prompt-output")

    args = parser.parse_args()

    fuzzer_stats = read_text_file(args.fuzzer_stats)
    harness_code = read_text_file(args.harness_code)
    source_context = read_text_file(args.source_context)
    sanitizer_output = read_text_file(args.sanitizer_output)
    notes = args.notes or "Not provided."

    report = build_guarded_triage_report(
        target_name=args.target_name,
        crash_type=args.crash_type,
        fuzzer_stats=fuzzer_stats,
        harness_code=harness_code,
        source_context=source_context,
        sanitizer_output=sanitizer_output,
        notes=notes,
    )

    write_output(args.output, report)

    if args.prompt_output:
        template = load_prompt_template(args.prompt_template)
        prompt = build_llm_prompt(
            template=template,
            target_name=args.target_name,
            crash_type=args.crash_type,
            fuzzer_stats=fuzzer_stats,
            harness_code=harness_code,
            source_context=source_context,
            sanitizer_output=sanitizer_output,
            notes=notes,
        )
        write_output(args.prompt_output, prompt)


if __name__ == "__main__":
    main()
