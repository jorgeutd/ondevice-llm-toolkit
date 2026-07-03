# Quantization cheatsheet

Quantization trades model quality for memory and speed. The right question
is never "which quant is best" but "how much quality does my task lose at
each size, and does it still fit my latency/memory budget" — measure both
sides.

## Formats by ecosystem

| Format | Ecosystem | Typical use |
|---|---|---|
| GGUF K-quants (Q4_K_M, Q5_K_M, Q6_K, Q8_0) | llama.cpp, Ollama | CPU/Apple Silicon/edge; Q4_K_M is the common size/quality sweet spot |
| GGUF i-quants (IQ2/IQ3/IQ4 families) | llama.cpp | Squeezing larger models into small memory; quality drops faster below ~3 bits |
| AWQ / GPTQ (4-bit) | vLLM, SGLang | GPU serving of weight-quantized checkpoints |
| FP8 (weights and/or KV) | vLLM, SGLang, TensorRT-LLM | Near-lossless on recent GPUs (Hopper/Blackwell); prefer pre-quantized checkpoints |
| NVFP4 | TensorRT-LLM | Blackwell-generation 4-bit floating point |
| MLX 4-bit / 8-bit | MLX | Apple Silicon; use pre-converted mlx-community checkpoints |

## Rules of thumb (verify on your task)

- Memory for weights ≈ parameters × bits ÷ 8. A 7B model is ~14 GB at FP16,
  ~4.5 GB at Q4_K_M.
- Quality degradation is not linear: FP16 → Q8 is usually negligible,
  Q5 → Q4 is usually small, below Q4 degradation accelerates — and it hits
  *structured* capabilities (tool calling, JSON adherence, math) harder than
  fluent prose, which is exactly what perplexity numbers hide.
- Smaller models degrade more from quantization than larger ones at the same
  bit width.
- Don't forget the KV cache: at long contexts it can rival weight memory.
  llama.cpp can quantize KV (`--cache-type-k/-v q8_0`); vLLM/SGLang/TRT-LLM
  support FP8 KV. KV quantization below 8-bit measurably hurts long-context
  quality — test it.

## How to validate a quantization choice

1. Pick the metric your product cares about (task accuracy, tool-call
   success, JSON validity — not just perplexity).
2. Run the same eval on the FP16/FP8 reference and each candidate quant.
3. Benchmark speed and memory on the target hardware.
4. Choose the smallest quant whose quality delta is within your tolerance,
   with confidence intervals, not single runs.

Steps 1–2 are what [local-agent-bench](https://github.com/jorgeutd/local-agent-bench)
automates for agentic capabilities; step 3 is `llmstart bench` or
[ondevice-llm-toolkit](https://github.com/jorgeutd/ondevice-llm-toolkit) for
llama.cpp specifics.
