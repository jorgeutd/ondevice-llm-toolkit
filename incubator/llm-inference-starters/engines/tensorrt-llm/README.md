# TensorRT-LLM

NVIDIA's maximum-performance engine: compiled kernels, FP8/NVFP4 on recent
GPUs, in-flight batching. Highest performance ceiling, highest operational
complexity — reach for it when vLLM/SGLang throughput is no longer enough
and you control the hardware.

Upstream docs: [Quick start](https://nvidia.github.io/TensorRT-LLM/latest/quick-start-guide.html) · [trtllm-serve](https://nvidia.github.io/TensorRT-LLM/latest/commands/trtllm-serve/trtllm-serve.html) · [NGC containers](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/tensorrt-llm/containers/release)

## Serve (NGC release container)

Pin a concrete tag from the NGC catalog; `x.y.z` below is a placeholder.

```bash
docker run --rm -it --ipc host --gpus all \
  --ulimit memlock=-1 --ulimit stack=67108864 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -p 8000:8000 \
  nvcr.io/nvidia/tensorrt-llm/release:x.y.z

# inside the container:
trtllm-serve Qwen/Qwen2.5-1.5B-Instruct --host 0.0.0.0 --port 8000
```

## Flags that matter first

| Flag | Why |
|---|---|
| `--max_batch_size` | Concurrent sequence ceiling |
| `--max_num_tokens` | Token budget per scheduler iteration |
| `--kv_cache_free_gpu_memory_fraction 0.9` | VRAM fraction for KV cache |
| `--tp_size N` | Tensor parallelism across GPUs |
| `--extra_llm_api_options config.yml` | Fine-grained tuning via YAML |

Prefer NVIDIA's pre-quantized checkpoints (e.g. `nvidia/Qwen3-8B-FP8`) when
your GPU supports them — they skip a conversion step and are tuned upstream.

## Benchmark it

```bash
llmstart bench --base-url http://localhost:8000/v1 --model Qwen/Qwen2.5-1.5B-Instruct
```

NVIDIA also ships `trtllm-bench` inside the container for engine-native
throughput benchmarking.
