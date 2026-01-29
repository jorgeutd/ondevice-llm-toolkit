#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BIN_DIR="$ROOT_DIR/bin"

mkdir -p "$BIN_DIR"
clang++ -std=c++17 -O2 "$ROOT_DIR/native/odlt_run.cpp" -o "$BIN_DIR/odlt_run"

echo "Built $BIN_DIR/odlt_run"
