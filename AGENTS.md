# AGENTS.md

## Cursor Cloud specific instructions

This repo is a small **monorepo of two Python 3.10+ CLI projects** (Python 3.12
on the cloud image). Both are installed **editable** into the system Python via
the startup update script (`pip install --break-system-packages -e ...`), so
source edits are picked up without reinstalling. There is no virtualenv (the
`venv` module is not available on the base image and cannot be installed from
the update script).

| Project | Path | Package / CLI | Purpose |
|---|---|---|---|
| OnDevice LLM Toolkit (ODLT) | repo root | `odlt` (`src/odlt`) | macOS-first CLI to benchmark `llama.cpp` and manage GGUF models |
| local-agent-bench | `incubator/local-agent-bench` | `labench` (`src/labench`) | Statistical benchmark for tool-calling / structured-output on OpenAI-compatible endpoints |

Note: `incubator/` is delivery staging that is **not meant to be merged into
`main`** (see `incubator/README.md`); it is still a real, tested project and is
part of the dev environment here.

### Running the CLIs
Console scripts install to `~/.local/bin` (added to `PATH` via `~/.bashrc`).
In non-interactive shells that do not source `~/.bashrc`, invoke them
PATH-independently instead: `python3 -m odlt ...` and `python3 -m labench ...`.

### Lint / test / build (see each project's README for full command list)
- Tests: run `python3 -m pytest` from the **repo root** (ODLT) and from
  `incubator/local-agent-bench` (labench). Both suites are self-contained (no
  network/model needed).
- Lint: `ruff` is configured for **labench only** — run `ruff check .` inside
  `incubator/local-agent-bench`. ODLT has no configured linter.

### Non-obvious caveats
- **ODLT is macOS-first and its heavy commands are not runnable in the cloud
  as-is.** `odlt bench run`, `odlt gguf smoke`, and `odlt deps build-llama`
  require cloning + building `llama.cpp` and a multi-GB GGUF download (network).
  The cross-platform, cloud-runnable surface is `odlt gguf verify` and
  `odlt gguf manifest` (work on any local file), plus the test suite. Set
  `ODLT_HOME` to relocate the `~/.ondevice-llm-toolkit` config/data dir.
- **The optional native helper** (`scripts/build_native.sh`) hardcodes
  `clang++`. On this image clang defaults to the gcc-14 toolchain, so it needs
  `libstdc++-14-dev` installed (only `libstdc++-13-dev` ships by default) or it
  fails with `'chrono' file not found`. `g++ -std=c++17 -O2 native/odlt_run.cpp
  -o bin/odlt_run` compiles it without that package. The helper is optional; the
  Python CLI runs without it.
- **`labench run` needs a live OpenAI-compatible endpoint** (`/v1/chat/
  completions`) — e.g. `llama-server`, vLLM, SGLang, Ollama. To exercise the
  full `run → report → compare` pipeline without a real model, point
  `--base-url` at a small mock server that returns tool calls / JSON per task.
  `labench tasks`/`report`/`compare` need no server.
