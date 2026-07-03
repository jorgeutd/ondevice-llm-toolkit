# Choosing an inference engine

There is no "best" engine — there is a best engine *for a workload on given
hardware with a given ops budget*. Work through the questions in order.

## 1. What hardware serves the model?

| Hardware | Candidates |
|---|---|
| NVIDIA datacenter GPUs (A100/H100/B200...) | vLLM, SGLang, TensorRT-LLM |
| NVIDIA consumer GPUs | vLLM, SGLang, llama.cpp (CUDA), Ollama |
| Apple Silicon | llama.cpp (Metal), MLX, Ollama |
| CPU only / edge devices | llama.cpp, Ollama |
| AMD GPUs | vLLM (ROCm), llama.cpp (Vulkan/ROCm) |

## 2. What does the traffic look like?

- **Many concurrent users, throughput-bound** → vLLM or SGLang. Continuous
  batching dominates every other optimization at high concurrency.
- **Many requests sharing long prefixes** (agents with big system prompts,
  RAG, few-shot) → SGLang's RadixAttention prefix caching is purpose-built
  for this; vLLM's prefix caching also helps.
- **Single user / low concurrency, latency-bound** (local apps, on-device
  assistants) → llama.cpp or MLX. Batching machinery buys you nothing at
  concurrency 1.
- **Absolute maximum throughput per GPU dollar, and you can invest ops
  effort** → TensorRT-LLM, ideally with NVIDIA's pre-quantized FP8/NVFP4
  checkpoints.

## 3. How much operational complexity can you carry?

Roughly increasing order: **Ollama → llama.cpp → MLX → vLLM → SGLang →
TensorRT-LLM**. If you're prototyping, start at the left and move right only
when measurements say you must.

## 4. Which features are hard requirements?

| Requirement | Notes |
|---|---|
| Tool / function calling | vLLM, SGLang, llama.cpp (`--jinja` + capable model), Ollama — verify with a tool-capable model, then measure quality with something like [local-agent-bench](https://github.com/jorgeutd/local-agent-bench) |
| Constrained JSON output | All six support some form; llama.cpp's GBNF grammars are the strongest hard guarantee on-device |
| Multi-GPU tensor parallelism | vLLM, SGLang, TensorRT-LLM |
| GGUF quantized models | llama.cpp, Ollama |
| LoRA adapters at serve time | vLLM, SGLang, TensorRT-LLM |

## 5. Then measure

Whatever the tables say, the decision is settled by measurement on your
model, your prompts, your hardware:

```bash
llmstart bench --base-url <endpoint> --model <model> --requests 10
```

Compare TTFT p95 and decode tokens/sec p50 across candidate engines at the
concurrency you actually expect. A single-request benchmark does not predict
behavior under load — for production sizing, follow up with a load test at
target QPS.
