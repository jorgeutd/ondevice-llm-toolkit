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

## 2. `profile/README.md` → `jorgeutd/jorgeutd`

Replaces your profile README (last updated April 2024) with one that
reflects your current agents / on-device inference / MCP work:

```bash
git clone https://github.com/jorgeutd/jorgeutd /tmp/profile
cp /tmp/staging/incubator/profile/README.md /tmp/profile/README.md
cd /tmp/profile
git add README.md && git commit -m "docs: refresh profile with agents and on-device inference work" && git push
```

Review the featured-projects section before pushing: the
`local-agent-bench` link only becomes valid after step 1.

## 3. Clean up

After both extractions, close the PR and delete this branch — none of
this content belongs in `ondevice-llm-toolkit` main.
