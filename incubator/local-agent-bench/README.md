# local-agent-bench

Statistical benchmark for **tool calling** and **structured outputs** on local LLMs.

Speed benchmarks for quantized models are everywhere. What's much harder to find is a rigorous answer to the question that actually decides whether you can ship an on-device agent: *does my Q4 model still call the right tool with the right arguments, and does it still emit schema-valid JSON?* `local-agent-bench` measures exactly that, against any OpenAI-compatible endpoint, and reports pass rates with proper confidence intervals instead of bare percentages.

Works with:

- [llama.cpp](https://github.com/ggml-org/llama.cpp) `llama-server`
- [vLLM](https://github.com/vllm-project/vllm)
- [SGLang](https://github.com/sgl-project/sglang)
- Ollama, LM Studio, and any other OpenAI-compatible server
- Hosted APIs (for baseline comparison against frontier models)

## What it measures

| Category | Question it answers | Failure modes it detects |
|---|---|---|
| `tool_call` | Does the model call the correct tool with correct arguments? | wrong tool, wrong/malformed arguments, answering instead of calling, multiple spurious calls |
| `no_tool` | Does the model abstain from tools when it should answer directly? | unnecessary tool calls (a common and costly agent failure) |
| `structured_output` | Does the model emit JSON conforming to a schema? | invalid JSON, schema violations, extra properties |

Every attempt is scored pass/fail with a stable failure-reason code, so reports show *why* a model fails, not just how often.

## Statistical honesty

- Pass rates are reported with **Wilson score intervals** (correct coverage at small n and extreme rates, unlike the normal approximation).
- `labench compare` uses a **seeded percentile bootstrap** on the pass-rate difference between two runs, so "Q4 dropped 6 points vs Q8" comes with a confidence interval instead of vibes.
- Runs default to `temperature=0` with a fixed seed for reproducibility where the server honors it.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]

# Serve a model, e.g. with llama.cpp (requires a chat template with tool support):
# llama-server -m qwen2.5-1.5b-instruct-q4_k_m.gguf --jinja --port 8080

# Run the suite (3 attempts per task by default)
labench run --base-url http://localhost:8080/v1 --model qwen2.5-1.5b-q4_k_m \
  --out runs/qwen-q4.json

# Render a Markdown report
labench report runs/qwen-q4.json --out reports/qwen-q4.md

# Compare two quantizations with a bootstrap CI
labench run --base-url http://localhost:8080/v1 --model qwen2.5-1.5b-q8_0 \
  --out runs/qwen-q8.json
labench compare runs/qwen-q8.json runs/qwen-q4.json
```

## Example report

```text
| Category          | Pass | n  | Pass rate | 95% CI (Wilson)  |
|-------------------|------|----|-----------|------------------|
| no_tool           | 8    | 9  | 88.9%     | [56.5%, 98.0%]   |
| structured_output | 7    | 9  | 77.8%     | [45.3%, 93.7%]   |
| tool_call         | 15   | 18 | 83.3%     | [60.8%, 94.2%]   |
| overall           | 30   | 36 | 83.3%     | [68.1%, 92.1%]   |

Failure breakdown:
- unexpected_tool_call: 3
- invalid_json: 2
- wrong_arguments: 1
```

## Adding tasks

Tasks are plain YAML in `tasks/` — no code required:

```yaml
- id: tc-100-my-task
  category: tool_call
  prompt: "Look up order 4711."
  tools:
    - type: function
      function:
        name: get_order
        parameters:
          type: object
          properties:
            order_id: { type: string }
          required: [order_id]
  expected:
    tool_name: get_order
    arguments: { order_id: "4711" }
    argument_match: exact
```

See `tasks/core.yaml` for the built-in suite and all three categories.

## Development

```bash
pip install -e .[dev]
ruff check .
pytest
```

## Roadmap

- Multi-turn tool-use tasks (call, observe result, respond)
- Parallel tool-call tasks
- MCP server tool-listing integration (benchmark against a live MCP toolset)
- Grammar-constrained decoding comparison (GBNF / `response_format` on vs. off)
- Model matrix runner: one command, N quantizations, one comparison table

## License

MIT
