# Ollama

The lowest-friction way to run local models: built-in model registry,
automatic GPU/Metal detection, and an OpenAI-compatible endpoint at
`http://localhost:11434/v1`.

Upstream docs: [ollama.com/download](https://ollama.com/download) · [OpenAI compatibility](https://github.com/ollama/ollama/blob/main/docs/openai.md)

## Serve

```bash
# Install from ollama.com, then:
ollama pull qwen2.5:1.5b
ollama serve   # usually already running as a service after install
curl http://localhost:11434/v1/models
```

## Custom model configuration (Modelfile)

Pin decoding parameters or a system prompt into a named model:

```bash
ollama create my-qwen -f Modelfile
ollama run my-qwen
```

## Environment variables that matter first

| Variable | Why |
|---|---|
| `OLLAMA_NUM_PARALLEL` | Concurrent request slots per model |
| `OLLAMA_MAX_LOADED_MODELS` | How many models stay resident |
| `OLLAMA_KEEP_ALIVE` | How long a model stays in memory after last use |

## Benchmark it

```bash
llmstart bench --base-url http://localhost:11434/v1 --model qwen2.5:1.5b
```

Trade-off vs. llama.cpp directly: Ollama is simpler to operate but exposes
fewer low-level controls (grammars, KV-cache quantization flags). It uses
llama.cpp under the hood.
