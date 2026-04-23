#!/usr/bin/env bash
# npc: plays a random NPC voice clip for the given lifecycle event.
# Usage: play.sh <EventName>
# Always exits 0 — a broken hook must never interrupt Claude Code.
set +e

EVENT="$1"
[[ -z "$EVENT" ]] && exit 0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$SCRIPT_DIR")}"
CONFIG_FILE="${NPC_CONFIG:-$HOME/.claude/npc.json}"

# ---------------------------------------------------------------------------
# Config + theme resolution
# ---------------------------------------------------------------------------
# Python owns the language-detection subprocess so it only runs when needed
# (not on every event when the user has set an explicit language).
_config_out=$(
  _NPC_CFG="$CONFIG_FILE" \
  _NPC_EVENT="$EVENT" \
  _NPC_PLUGIN_ROOT="$PLUGIN_ROOT" \
  python3 - <<'PYEOF' 2>/dev/null
import json, os, subprocess
try:
    try:
        with open(os.environ['_NPC_CFG']) as f:
            c = json.load(f)
    except Exception:
        c = {}

    ev = os.environ.get('_NPC_EVENT', '')
    plugin_root = os.environ.get('_NPC_PLUGIN_ROOT', '')
    theme = str(c.get('theme', 'warcraft3'))
    enabled = str(c.get('enabled', True)).lower()
    event_enabled = str(c.get('events', {}).get(ev, True)).lower()
    probability = str(c.get('probability', {}).get(ev, 1.0))
    volume = str(int(c.get('volume', 20)))

    user_lang = c.get('language', None)
    if user_lang in (None, '', 'auto'):
        try:
            r = subprocess.run(
                ['bash', os.path.join(plugin_root, 'hooks', 'detect-lang.sh')],
                capture_output=True, text=True, timeout=2,
            )
            user_lang = r.stdout.strip()
        except Exception:
            user_lang = ''
    user_lang = str(user_lang).lower()

    lang_code = ''
    try:
        with open(os.path.join(plugin_root, 'sounds', theme, 'theme.json')) as f:
            tm = json.load(f)
        languages = [str(l).lower() for l in tm.get('languages', []) if l]
        default_lang = str(tm.get('defaultLanguage', '')).lower()
        if languages and default_lang:
            lang_code = user_lang if user_lang in languages else default_lang
    except Exception:
        pass

    print('|'.join([theme, enabled, event_enabled, probability, volume, lang_code]))
except Exception:
    print('warcraft3|true|true|1.0|20|')
PYEOF
)
IFS='|' read -r THEME ENABLED EVENT_ENABLED PROBABILITY VOLUME LANG_CODE \
  <<< "${_config_out:-warcraft3|true|true|1.0|20|}"

# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------
[[ "$ENABLED" != "true" ]] && exit 0
[[ "$EVENT_ENABLED" != "true" ]] && exit 0
# Empty LANG_CODE means the theme is missing, malformed, or declared no usable language.
[[ -z "$LANG_CODE" ]] && exit 0

# Probability roll — single awk handles both the roll and the play/skip decision.
PROB_CHECK=$(awk -v seed="$(( $$ * 32768 + RANDOM ))" -v p="$PROBABILITY" \
  'BEGIN{srand(seed); print (rand() <= p) ? "play" : "skip"}')
[[ "$PROB_CHECK" != "play" ]] && exit 0

# ---------------------------------------------------------------------------
# Resolve clip directory and play
# ---------------------------------------------------------------------------
CLIP_DIR="${PLUGIN_ROOT}/sounds/${THEME}/${LANG_CODE}/${EVENT}"
[[ ! -d "$CLIP_DIR" ]] && exit 0

CLIPS=()
for f in "$CLIP_DIR"/*.mp3; do
  [[ -f "$f" ]] && CLIPS+=("$f")
done
[[ ${#CLIPS[@]} -eq 0 ]] && exit 0

CLIP="${CLIPS[RANDOM % ${#CLIPS[@]}]}"
read -r VOLUME_FLOAT VOLUME_SCALE < <(awk -v v="$VOLUME" 'BEGIN{printf "%.2f %d\n", v/100, v*327}')

play_clip() {
  local file="$1"
  if command -v afplay >/dev/null 2>&1; then
    afplay -v "$VOLUME_FLOAT" "$file" &
  elif command -v mpg123 >/dev/null 2>&1; then
    mpg123 -q --scale "$VOLUME_SCALE" "$file" &
  elif command -v ffplay >/dev/null 2>&1; then
    ffplay -nodisp -autoexit -loglevel quiet -af "volume=$VOLUME_FLOAT" "$file" &
  elif command -v mplayer >/dev/null 2>&1; then
    mplayer -really-quiet -volume "$VOLUME" "$file" &
  elif command -v cvlc >/dev/null 2>&1; then
    cvlc --play-and-exit --gain "$VOLUME_FLOAT" "$file" &
  elif command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -c "(New-Object Media.SoundPlayer '$file').PlaySync()" &
  fi
}

play_clip "$CLIP" 2>/dev/null

exit 0
