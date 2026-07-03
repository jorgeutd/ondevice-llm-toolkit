#!/usr/bin/env bash
# Serve an MLX model with mlx_lm.server (OpenAI-compatible on :8080).
# Usage: ./serve.sh [model-id] [extra mlx_lm.server args...]
set -euo pipefail

MODEL_ID="${1:-mlx-community/Qwen2.5-1.5B-Instruct-4bit}"
[[ $# -gt 0 ]] && shift

if ! command -v mlx_lm.server >/dev/null 2>&1; then
  echo "error: mlx_lm.server not found. Install with 'pip install mlx-lm' (Apple Silicon only)." >&2
  exit 1
fi

exec mlx_lm.server \
  --model "$MODEL_ID" \
  --host 127.0.0.1 \
  --port 8080 \
  "$@"
