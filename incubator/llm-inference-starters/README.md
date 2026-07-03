# llm-inference-starters

Production-oriented starter code and deployment recipes for LLM inference engines, plus a tiny client (`llmstart`) that probes any OpenAI-compatible endpoint and measures **time to first token** and **decode tokens/sec** — so you compare engines with numbers, not vibes.

## Engines covered

| Engine | Best for | Hardware | Default port | Recipe |
|---|---|---|---|---|
| [vLLM](engines/vllm/) | High-throughput GPU serving, production APIs | NVIDIA (ROCm variant) | 8000 | Docker Compose |
| [SGLang](engines/sglang/) | High throughput + RadixAttention prefix caching | NVIDIA | 30000 | Docker Compose |
| [llama.cpp](engines/llama-cpp/) | CPU / Apple Silicon / edge, GGUF quantization | Any (Metal, CUDA, Vulkan, CPU) | 8080 | `llama-server` script |
| [Ollama](engines/ollama/) | Easiest local start, model management | Any | 11434 | CLI + Modelfile |
| [TensorRT-LLM](engines/tensorrt-llm/) | Max NVIDIA performance, FP8/FP4 on latest GPUs | NVIDIA | 8000 | NGC container + `trtllm-serve` |
| [MLX](engines/mlx/) | Apple Silicon unified-memory serving | Apple Silicon | 8080 | `mlx_lm.server` script |

All six expose an OpenAI-compatible `/v1/chat/completions` endpoint, so the client code in `examples/` and the `llmstart` tool work unchanged against every one of them.

## Quickstart

Pick an engine and start it (each folder has a copy-paste recipe). Example with llama.cpp:

```bash
# see engines/llama-cpp/README.md for install options
./engines/llama-cpp/serve.sh ~/models/qwen2.5-1.5b-instruct-q4_k_m.gguf
```

Install the client tooling and point it at the endpoint:

```bash
pip install -e common/

llmstart probe --base-url http://localhost:8080/v1
llmstart bench --base-url http://localhost:8080/v1 --model qwen2.5-1.5b \
  --requests 5 --max-tokens 128
```

Sample output:

```text
            Benchmark: qwen2.5-1.5b (5 requests)
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━┓
┃ metric               ┃    p50 ┃    p95 ┃    max ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━┩
│ time to first token  │ 0.142s │ 0.187s │ 0.191s │
│ decode tokens/sec    │   58.3 │   55.1 │   54.7 │
│ total request time   │ 2.31s  │ 2.48s  │ 2.50s  │
└──────────────────────┴────────┴────────┴────────┘
token counts from: server usage field
```

## Starter examples

Runnable against any of the engines (`pip install openai` first):

- [`examples/chat_streaming.py`](examples/chat_streaming.py) — streaming chat with token-by-token output
- [`examples/structured_output.py`](examples/structured_output.py) — JSON-schema-constrained responses
- [`examples/tool_calling.py`](examples/tool_calling.py) — function calling with a tool-result round trip

```bash
python examples/chat_streaming.py --base-url http://localhost:8000/v1 --model Qwen/Qwen2.5-1.5B-Instruct
```

## Docs

- [Choosing an engine](docs/choosing-an-engine.md) — decision guide: throughput vs. latency vs. hardware vs. ops burden
- [Quantization cheatsheet](docs/quantization-cheatsheet.md) — GGUF K-quants, AWQ, GPTQ, FP8, MLX 4-bit, KV-cache quantization

## Measurement notes

- TTFT is wall-clock from request start to the first content delta.
- Decode tokens/sec = completion tokens ÷ (last token time − first token time); prefill is excluded so the number reflects steady-state generation.
- Token counts come from the server's `usage` field (`stream_options: {"include_usage": true}`) when available, otherwise fall back to counting stream chunks — the report labels which source was used.
- Engine commands in this repo were verified against the official docs at the time of writing; engines move fast, so each recipe links to the upstream doc it came from.

## Development

```bash
pip install -e "common/[dev]"
ruff check common/
pytest common/
```

## License

MIT
