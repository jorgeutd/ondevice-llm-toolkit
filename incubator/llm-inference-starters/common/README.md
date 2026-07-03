# llmstart

Small client and CLI for probing and micro-benchmarking any OpenAI-compatible
inference endpoint. See the [repository README](../README.md) for usage and
the metric definitions (TTFT, decode tokens/sec).

```bash
pip install -e ".[dev]"
ruff check .
pytest
```
