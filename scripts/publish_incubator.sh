#!/usr/bin/env bash
# Publish the incubator/ staging content to its final destinations:
#   1. incubator/local-agent-bench      -> github.com/<owner>/local-agent-bench   (new repo)
#   2. incubator/llm-inference-starters -> github.com/<owner>/llm-inference-starters (new repo)
#   3. incubator/profile/README.md      -> github.com/<owner>/<owner> profile README
#
# Requirements: git and gh (authenticated as the target owner).
# Idempotent: existing repos are skipped, the profile is only pushed on change.
#
# Usage: ./scripts/publish_incubator.sh
set -euo pipefail

OWNER="${PUBLISH_OWNER:-jorgeutd}"

# Cursor Cloud Agents inject secrets as environment variables. If gh has no
# token yet, adopt one from the known secret names (most specific first).
if [[ -z "${GH_TOKEN:-}" ]]; then
  for candidate in github-publish GITHUB_PUBLISH GITHUB-PUBLISH GH_USER_TOKEN; do
    value="$(printenv "$candidate" 2>/dev/null || true)"
    if [[ -n "$value" ]]; then
      export GH_TOKEN="$value"
      echo "using token from secret: $candidate"
      break
    fi
  done
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
INCUBATOR="$REPO_ROOT/incubator"

fail() { echo "error: $*" >&2; exit 1; }

[[ -d "$INCUBATOR" ]] || fail "incubator directory not found at $INCUBATOR"
command -v gh >/dev/null 2>&1 || fail "gh CLI not installed (https://cli.github.com)"
gh auth status >/dev/null 2>&1 || fail "gh is not authenticated; run 'gh auth login' first"

LOGIN="$(gh api user --jq .login 2>/dev/null || true)"
if [[ -z "$LOGIN" || "$LOGIN" == *"{"* ]]; then
  fail "the available token is not a personal one (app/installation tokens cannot create user repos); run this from a machine where gh is logged in as $OWNER"
fi
[[ "$LOGIN" == "$OWNER" ]] || fail "gh is authenticated as '$LOGIN' but target owner is '$OWNER' (set PUBLISH_OWNER to override)"

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

publish_project() {
  local name="$1" description="$2"
  if gh repo view "$OWNER/$name" >/dev/null 2>&1; then
    echo "skip: $OWNER/$name already exists"
    return
  fi
  echo "creating $OWNER/$name ..."
  local staging="$WORKDIR/$name"
  cp -R "$INCUBATOR/$name" "$staging"
  git -C "$staging" init -q -b main
  git -C "$staging" add -A
  git -C "$staging" commit -q -m "feat: initial release of $name"
  gh repo create "$OWNER/$name" --public --source "$staging" --push \
    --description "$description"
  echo "done: https://github.com/$OWNER/$name"
}

update_profile() {
  local profile_src="$INCUBATOR/profile/README.md"
  [[ -f "$profile_src" ]] || fail "profile README not found at $profile_src"
  local clone_dir="$WORKDIR/profile-repo"
  if ! gh repo clone "$OWNER/$OWNER" "$clone_dir" -- -q 2>/dev/null; then
    fail "could not clone $OWNER/$OWNER (create the profile repo on GitHub first)"
  fi
  cp "$profile_src" "$clone_dir/README.md"
  if git -C "$clone_dir" diff --quiet; then
    echo "skip: profile README already up to date"
    return
  fi
  git -C "$clone_dir" add README.md
  git -C "$clone_dir" commit -q -m "docs: refresh profile with agents and llm inference work"
  # Route the push through gh's credential helper so the personal token is
  # used even when the machine has a different global git credential helper.
  git -C "$clone_dir" -c credential.helper= \
    -c 'credential.helper=!gh auth git-credential' push -q
  echo "done: profile README updated at https://github.com/$OWNER"
}

publish_project "local-agent-bench" \
  "Statistical benchmark for tool calling and structured outputs on local LLMs (llama.cpp, vLLM, SGLang, Ollama)"
publish_project "llm-inference-starters" \
  "Starter code and deployment recipes for LLM inference engines: vLLM, SGLang, llama.cpp, TensorRT-LLM, Ollama, MLX"
update_profile

cat <<'EOF'

All published. Optional cleanup in ondevice-llm-toolkit now that the
extracted repos are the source of truth:

  git rm -r incubator scripts/publish_incubator.sh
  git commit -m "chore: remove incubator staging after extraction"
  git push
EOF
