#!/usr/bin/env bash
# npc: thin shim — all logic lives in npc.py.
# Always exits 0 — a broken hook must never interrupt Claude Code.
set +e

EVENT="$1"
[[ -z "$EVENT" ]] && exit 0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$SCRIPT_DIR")}"

python3 "${SCRIPT_DIR}/npc.py" play "$EVENT" 2>/dev/null

exit 0
