# llama.cpp

The reference engine for CPU, Apple Silicon (Metal), and edge deployment.
Runs GGUF-quantized models; supports grammar-constrained decoding (GBNF) for
production-grade structured outputs.

Upstream docs: [llama-server README](https://github.com/ggml-org/llama.cpp/tree/master/tools/server) · [Build guide](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md)

## Install

```bash
brew install llama.cpp        # macOS
# or build from source for CUDA/Vulkan:
# cmake -B build -DGGML_CUDA=ON && cmake --build build --config Release
```

## Serve

```bash
# Download a GGUF (or point at one you already have)
./serve.sh ~/models/qwen2.5-1.5b-instruct-q4_k_m.gguf

# llama-server can also pull directly from Hugging Face:
llama-server -hf Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m --jinja --port 8080
```

`--jinja` enables the model's chat template, which is required for
OpenAI-style tool calling on models that support it.

## Flags that matter first

| Flag | Why |
|---|---|
| `-ngl 99` | Offload all layers to GPU/Metal (default is CPU) |
| `-c 8192` | Context window size (KV cache memory scales with it) |
| `--jinja` | Use the model's chat template; needed for tool calls |
| `-t N` | CPU thread count for CPU inference |
| `--api-key <key>` | Require auth before exposing beyond localhost |

## Benchmark it

```bash
llmstart bench --base-url http://localhost:8080/v1 --model qwen2.5-1.5b
```

For deeper llama.cpp-specific benchmarking (prompt-processing vs. generation
splits per quantization), see
[ondevice-llm-toolkit](https://github.com/jorgeutd/ondevice-llm-toolkit).
