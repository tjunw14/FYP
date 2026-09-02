#!/usr/bin/env bash
set -euo pipefail

ROOT="${FYP_ROOT:-/work}"
OPEN5GS_DIR="${OPEN5GS_DIR:-$ROOT/external/open5gs}"
HARNESS_SOURCE="${HARNESS_SOURCE:-$ROOT/targets/open5gs/harness_registration_request.c}"
HARNESS_BINARY="${HARNESS_BINARY:-$ROOT/targets/open5gs/harness_registration_request}"

if [[ ! -d "$OPEN5GS_DIR" ]]; then
  echo "Open5GS source tree not found: $OPEN5GS_DIR" >&2
  echo "Place the Open5GS checkout under external/open5gs before building." >&2
  exit 1
fi

if [[ ! -f "$HARNESS_SOURCE" ]]; then
  echo "Harness source not found: $HARNESS_SOURCE" >&2
  exit 1
fi

if [[ ! -f "$OPEN5GS_DIR/build/lib/nas/5gs/libogsnas-5gs.so" ]]; then
  echo "Instrumented Open5GS build artifacts were not found under $OPEN5GS_DIR/build." >&2
  echo "Build Open5GS first, then rerun this script." >&2
  exit 1
fi

cd "$OPEN5GS_DIR"

afl-clang-fast \
  -O1 -g \
  -fsanitize=address,undefined \
  -fno-omit-frame-pointer \
  -Ilib \
  -Ibuild/lib \
  -Ilib/core \
  -Ibuild/lib/core \
  -Ilib/nas \
  -Ilib/nas/common \
  -Ibuild/lib/nas/common \
  -Ilib/nas/5gs \
  -Ibuild/lib/nas/5gs \
  $(pkg-config --cflags talloc) \
  "$HARNESS_SOURCE" \
  -Lbuild/lib/nas/5gs -logsnas-5gs \
  -Lbuild/lib/nas/common -logsnas-common \
  -Lbuild/lib/core -logscore \
  $(pkg-config --libs talloc) \
  -Wl,-rpath,"$OPEN5GS_DIR/build/lib/nas/5gs" \
  -Wl,-rpath,"$OPEN5GS_DIR/build/lib/nas/common" \
  -Wl,-rpath,"$OPEN5GS_DIR/build/lib/core" \
  -o "$HARNESS_BINARY"

printf 'Built AFL++ Open5GS harness: %s\n' "$HARNESS_BINARY"
