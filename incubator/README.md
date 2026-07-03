# Incubator (delivery staging — do not merge to main)

This directory is a delivery vehicle for content destined for **other**
repositories. It exists because this workspace only has push access to
`ondevice-llm-toolkit`. Extract the contents and delete the branch.

## 1. `local-agent-bench/` → new repository

A complete, tested project (37 passing tests, ruff-clean, CI workflow
included). To publish it as `jorgeutd/local-agent-bench`:

```bash
# from a machine with your GitHub credentials
git clone https://github.com/jorgeutd/ondevice-llm-toolkit --branch cursor/local-agent-bench-scaffold-1a10 /tmp/staging
cp -R /tmp/staging/incubator/local-agent-bench ~/local-agent-bench
cd ~/local-agent-bench
git init && git add -A && git commit -m "feat: initial release of local-agent-bench"
gh repo create jorgeutd/local-agent-bench --public --source . --push \
  --description "Statistical benchmark for tool calling and structured outputs on local LLMs"
```

Verify locally first if you like:

```bash
cd ~/local-agent-bench
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
ruff check . && pytest
```

## 2. `llm-inference-starters/` → new repository

Starter code and deployment recipes for six inference engines (vLLM, SGLang,
llama.cpp, TensorRT-LLM, Ollama, MLX) plus the `llmstart` micro-benchmark
CLI (21 passing tests, ruff-clean, shellcheck-clean, CI included). To
publish as `jorgeutd/llm-inference-starters`:

```bash
cp -R /tmp/staging/incubator/llm-inference-starters ~/llm-inference-starters
cd ~/llm-inference-starters
git init && git add -A && git commit -m "feat: initial release of llm-inference-starters"
gh repo create jorgeutd/llm-inference-starters --public --source . --push \
  --description "Starter code and deployment recipes for LLM inference engines: vLLM, SGLang, llama.cpp, TensorRT-LLM, Ollama, MLX"
```

Verify locally first if you like:

```bash
cd ~/llm-inference-starters
python -m venv .venv && source .venv/bin/activate
pip install -e "common/[dev]"
ruff check common/ examples/ && pytest common/
```

## 3. `profile/README.md` → `jorgeutd/jorgeutd`

Replaces your profile README (last updated April 2024) with one that
reflects your current agents / on-device inference / MCP work:

```bash
git clone https://github.com/jorgeutd/jorgeutd /tmp/profile
cp /tmp/staging/incubator/profile/README.md /tmp/profile/README.md
cd /tmp/profile
git add README.md && git commit -m "docs: refresh profile with agents and on-device inference work" && git push
```

Review the featured-projects section before pushing: the
`local-agent-bench` and `llm-inference-starters` links only become valid
after steps 1 and 2.

## 4. Clean up

After the extractions, close the PR and delete this branch — none of
this content belongs in `ondevice-llm-toolkit` main.
