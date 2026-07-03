# vLLM

High-throughput GPU serving with PagedAttention and continuous batching. The
default choice for production OpenAI-compatible APIs on NVIDIA hardware.

Upstream docs: [Quickstart](https://docs.vllm.ai/en/stable/getting_started/quickstart/) · [Docker](https://docs.vllm.ai/en/stable/deployment/docker/)

## Docker Compose (recommended)

```bash
export MODEL_ID=Qwen/Qwen2.5-1.5B-Instruct   # any HF model id
docker compose up -d
curl http://localhost:8000/v1/models
```

## Bare pip

```bash
pip install vllm   # or: uv run --with vllm vllm serve ...
vllm serve Qwen/Qwen2.5-1.5B-Instruct
```

## Flags that matter first

| Flag | Why |
|---|---|
| `--gpu-memory-utilization 0.90` | Fraction of VRAM vLLM may claim (weights + KV cache) |
| `--max-model-len 8192` | Cap context to fit more concurrent sequences in KV cache |
| `--tensor-parallel-size N` | Shard across N GPUs when the model doesn't fit on one |
| `--api-key <key>` | Require auth — do this before exposing beyond localhost |

## Benchmark it

```bash
llmstart bench --base-url http://localhost:8000/v1 --model "$MODEL_ID"
```
