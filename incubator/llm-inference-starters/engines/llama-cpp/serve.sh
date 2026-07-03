#!/usr/bin/env bash
# Serve a local GGUF model with llama-server (OpenAI-compatible on :8080).
# Usage: ./serve.sh /path/to/model.gguf [extra llama-server args...]
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 /path/to/model.gguf [extra llama-server args...]" >&2
  exit 1
fi

MODEL_PATH="$1"
shift

if [[ ! -f "$MODEL_PATH" ]]; then
  echo "error: model file not found: $MODEL_PATH" >&2
  exit 1
fi

if ! command -v llama-server >/dev/null 2>&1; then
  echo "error: llama-server not found. Install with 'brew install llama.cpp' or build from source." >&2
  exit 1
fi

exec llama-server \
  -m "$MODEL_PATH" \
  --host 127.0.0.1 \
  --port 8080 \
  -ngl 99 \
  -c 8192 \
  --jinja \
  "$@"
