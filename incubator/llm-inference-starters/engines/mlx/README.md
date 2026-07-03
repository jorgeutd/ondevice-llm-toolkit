# MLX (Apple Silicon)

Apple's array framework with first-class LLM support (`mlx-lm`). Uses unified
memory — no CPU/GPU transfer — and is often the fastest option for
Apple-Silicon-only deployment. Models come pre-converted from the
[mlx-community](https://huggingface.co/mlx-community) hub organization.

Upstream docs: [mlx-lm README](https://github.com/ml-explore/mlx-lm) · [server docs](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/SERVER.md)

## Serve

```bash
pip install mlx-lm
./serve.sh mlx-community/Qwen2.5-1.5B-Instruct-4bit
curl http://localhost:8080/v1/models
```

Note: the `mlx_lm.server` is explicitly not hardened for production exposure;
keep it on localhost or behind a reverse proxy you control.

## One-off generation without a server

```bash
mlx_lm.generate --model mlx-community/Qwen2.5-1.5B-Instruct-4bit \
  --prompt "Explain KV cache in two sentences."
```

## Benchmark it

```bash
llmstart bench --base-url http://localhost:8080/v1 \
  --model mlx-community/Qwen2.5-1.5B-Instruct-4bit
```

Compare against llama.cpp/Metal on the same machine — the winner varies by
model size, quantization, and prompt length, so measure your workload.
