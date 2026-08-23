#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/run_open5gs_fuzz.sh <seed-dir> <output-dir> <duration> <report-dir> [dictionary]

Arguments may be absolute paths or paths relative to /work.
Use '-' as the dictionary argument to run without a dictionary.

Example:
  scripts/run_open5gs_fuzz.sh \
    targets/open5gs/seeds_registration_webllm \
    targets/open5gs/out_registration_webllm_15m \
    15m \
    reports/open5gs/phase5_webllm_demo \
    -
EOF
}

if [[ $# -lt 4 || $# -gt 5 ]]; then
  usage
  exit 2
fi

ROOT="${FYP_ROOT:-/work}"
HARNESS="${HARNESS_BINARY:-$ROOT/targets/open5gs/harness_registration_request}"

resolve_path() {
  local value="$1"
  if [[ "$value" = /* ]]; then
    printf '%s\n' "$value"
  else
    printf '%s/%s\n' "$ROOT" "$value"
  fi
}

SEED_DIR="$(resolve_path "$1")"
OUT_DIR="$(resolve_path "$2")"
DURATION="$3"
REPORT_DIR="$(resolve_path "$4")"
DICT_ARG="${5:--}"

if [[ "$DICT_ARG" == "-" ]]; then
  DICTIONARY=""
else
  DICTIONARY="$(resolve_path "$DICT_ARG")"
fi

if [[ ! -x "$HARNESS" ]]; then
  echo "Harness binary not found or not executable: $HARNESS" >&2
  echo "Build it first with scripts/build_open5gs_harness.sh" >&2
  exit 1
fi

if [[ ! -d "$SEED_DIR" ]]; then
  echo "Seed directory not found: $SEED_DIR" >&2
  exit 1
fi

if ! compgen -G "$SEED_DIR/*.bin" > /dev/null; then
  echo "No .bin seed files found in: $SEED_DIR" >&2
  exit 1
fi

if [[ -n "$DICTIONARY" && ! -f "$DICTIONARY" ]]; then
  echo "AFL++ dictionary not found: $DICTIONARY" >&2
  exit 1
fi

TMP_CORPUS="$(mktemp -d /tmp/fyp-afl-seeds.XXXXXX)"
cleanup() {
  rm -rf "$TMP_CORPUS"
}
trap cleanup EXIT

cp "$SEED_DIR"/*.bin "$TMP_CORPUS"/
SEED_COUNT="$(find "$TMP_CORPUS" -maxdepth 1 -type f -name '*.bin' | wc -l | tr -d ' ')"

echo "Using $SEED_COUNT binary seed(s) from: $SEED_DIR"
echo "Harness: $HARNESS"
echo "Duration: $DURATION"
if [[ -n "$DICTIONARY" ]]; then
  echo "Dictionary: $DICTIONARY"
else
  echo "Dictionary: disabled"
fi

rm -rf "$OUT_DIR"
mkdir -p "$(dirname "$OUT_DIR")" "$REPORT_DIR"

AFL_CMD=(afl-fuzz -i "$TMP_CORPUS" -o "$OUT_DIR")
if [[ -n "$DICTIONARY" ]]; then
  AFL_CMD+=( -x "$DICTIONARY" )
fi
AFL_CMD+=( -- "$HARNESS" @@ )

set +e
timeout "$DURATION" "${AFL_CMD[@]}"
RUN_STATUS=$?
set -e

if [[ $RUN_STATUS -ne 0 && $RUN_STATUS -ne 124 ]]; then
  echo "AFL++ exited unexpectedly with status $RUN_STATUS" >&2
  exit "$RUN_STATUS"
fi

AFL_INSTANCE="$OUT_DIR/default"
if [[ ! -f "$AFL_INSTANCE/fuzzer_stats" ]]; then
  echo "AFL++ completed but fuzzer_stats was not found: $AFL_INSTANCE/fuzzer_stats" >&2
  exit 1
fi

PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}" \
  python3 -m fyp_llm_afl.results \
  --afl-instance "$AFL_INSTANCE" \
  --report-dir "$REPORT_DIR"

cp "$SEED_DIR"/*.bin "$REPORT_DIR"/ 2>/dev/null || true
if [[ -f "$SEED_DIR/manifest.csv" ]]; then
  cp "$SEED_DIR/manifest.csv" "$REPORT_DIR/seed_manifest.csv"
fi
if [[ -f "$SEED_DIR/summary.json" ]]; then
  cp "$SEED_DIR/summary.json" "$REPORT_DIR/seed_corpus_summary.json"
fi

printf '%s\n' "$SEED_COUNT" > "$REPORT_DIR/seed_count.txt"
printf '%s\n' "$DURATION" > "$REPORT_DIR/requested_duration.txt"

if [[ $RUN_STATUS -eq 124 ]]; then
  echo "Timed experiment completed normally after $DURATION."
else
  echo "AFL++ exited before the timeout with status 0."
fi

echo "Evidence directory: $REPORT_DIR"
