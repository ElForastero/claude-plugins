#!/usr/bin/env bash
# Validates every plugin manifest and the root marketplace manifest using the
# official Claude Code CLI validator. Exits non-zero if anything fails.

set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v claude >/dev/null 2>&1; then
  echo "error: 'claude' CLI not found. Install Claude Code: npm install -g @anthropic-ai/claude-code" >&2
  exit 2
fi

fail=0

echo "→ marketplace"
claude plugin validate . || fail=1

for dir in plugins/*/; do
  echo "→ ${dir%/}"
  claude plugin validate "$dir" || fail=1
done

exit "$fail"
