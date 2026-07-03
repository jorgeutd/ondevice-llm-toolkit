# SGLang

High-throughput serving with RadixAttention automatic prefix caching — strong
when many requests share long prompt prefixes (agents, RAG, few-shot).

Upstream docs: [Quickstart](https://docs.sglang.io/docs/get-started/quickstart) · [Install](https://docs.sglang.io/docs/get-started/install)

## Docker Compose (recommended)

```bash
export MODEL_ID=Qwen/Qwen2.5-1.5B-Instruct
docker compose up -d
curl http://localhost:30000/v1/models
```

The `latest-runtime` image variant is ~40% smaller for production; images
default to CUDA 13 — use the `-cu129` suffix tags on CUDA 12 hosts.

## Bare pip

```bash
pip install "sglang[all]"
python3 -m sglang.launch_server --model-path Qwen/Qwen2.5-1.5B-Instruct \
  --host 0.0.0.0 --port 30000
```

## Flags that matter first

| Flag | Why |
|---|---|
| `--mem-fraction-static 0.85` | VRAM fraction for weights + KV pool |
| `--context-length 8192` | Cap context length |
| `--tp 2` | Tensor parallelism across GPUs |
| `--api-key <key>` | Require auth before exposing beyond localhost |

## Benchmark it

```bash
llmstart bench --base-url http://localhost:30000/v1 --model "$MODEL_ID"
```
