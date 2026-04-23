#!/usr/bin/env bash
# npc: plays a random NPC voice clip for the given lifecycle event.
# Usage: play.sh <EventName>
# Always exits 0 — a broken hook must never interrupt Claude Code.
# Debug: set NPC_DEBUG=1 to append a trace to $TMPDIR/npc-debug.log.
set +e

EVENT="$1"
[[ -z "$EVENT" ]] && exit 0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$SCRIPT_DIR")}"
CONFIG_FILE="${NPC_CONFIG:-$HOME/.claude/npc.json}"
NPC_DEBUG_LOG="${TMPDIR:-/tmp}/npc-debug.log"

npc_debug() {
  [[ "$NPC_DEBUG" = "1" ]] || return 0
  printf '[%s] %s: %s\n' "$(date '+%H:%M:%S')" "$EVENT" "$*" >> "$NPC_DEBUG_LOG" 2>/dev/null
}
npc_debug "start (plugin_root=$PLUGIN_ROOT config=$CONFIG_FILE)"

# ---------------------------------------------------------------------------
# Config + theme resolution
# ---------------------------------------------------------------------------
# Python owns the language-detection subprocess so it only runs when needed
# (not on every event when the user has set an explicit language).
_config_out=$(
  _NPC_CFG="$CONFIG_FILE" \
  _NPC_EVENT="$EVENT" \
  _NPC_PLUGIN_ROOT="$PLUGIN_ROOT" \
  _NPC_DEBUG="$NPC_DEBUG" \
  _NPC_DEBUG_LOG="$NPC_DEBUG_LOG" \
  python3 - <<'PYEOF' 2>/dev/null
import json, os, subprocess

def _dbg(msg):
    if os.environ.get('_NPC_DEBUG') != '1':
        return
    try:
        with open(os.environ['_NPC_DEBUG_LOG'], 'a') as fh:
            fh.write('[py] ' + msg + '\n')
    except Exception:
        pass

def _truthy(v, default=True):
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    if isinstance(v, str):
        return v.strip().lower() not in ('', 'false', '0', 'no', 'off')
    return bool(v)

def _as_str(v, default):
    if v is None or (isinstance(v, str) and not v.strip()):
        return default
    return str(v)

def _as_int(v, default):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default

def _as_float(v, default):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default

try:
    try:
        with open(os.environ['_NPC_CFG']) as f:
            c = json.load(f)
        if not isinstance(c, dict):
            _dbg('config is not a JSON object, ignoring')
            c = {}
    except FileNotFoundError:
        c = {}
    except Exception as e:
        _dbg('config unreadable: ' + repr(e))
        c = {}

    ev = os.environ.get('_NPC_EVENT', '')
    plugin_root = os.environ.get('_NPC_PLUGIN_ROOT', '')

    theme = _as_str(c.get('theme'), 'warcraft3')
    enabled = 'true' if _truthy(c.get('enabled'), True) else 'false'

    events_map = c.get('events') if isinstance(c.get('events'), dict) else {}
    event_enabled = 'true' if _truthy(events_map.get(ev), True) else 'false'

    prob_map = c.get('probability') if isinstance(c.get('probability'), dict) else {}
    probability = str(_as_float(prob_map.get(ev), 1.0))

    volume = str(_as_int(c.get('volume'), 20))

    user_lang = c.get('language', None)
    if user_lang in (None, '', 'auto'):
        try:
            r = subprocess.run(
                ['bash', os.path.join(plugin_root, 'hooks', 'detect-lang.sh')],
                capture_output=True, text=True, timeout=2,
            )
            user_lang = r.stdout.strip()
        except Exception as e:
            _dbg('detect-lang failed: ' + repr(e))
            user_lang = ''
    user_lang = str(user_lang or '').lower()

    lang_code = ''
    theme_json_path = os.path.join(plugin_root, 'sounds', theme, 'theme.json')
    try:
        with open(theme_json_path) as f:
            tm = json.load(f)
        langs_raw = tm.get('languages') if isinstance(tm.get('languages'), list) else []
        languages = [str(l).lower() for l in langs_raw if l]
        default_lang = _as_str(tm.get('defaultLanguage'), '').lower()
        fallback = default_lang if default_lang in languages else (languages[0] if languages else '')
        if fallback:
            lang_code = user_lang if user_lang in languages else fallback
    except Exception as e:
        _dbg('theme.json read failed (' + theme_json_path + '): ' + repr(e))

    _dbg('resolved theme=' + theme + ' enabled=' + enabled
         + ' event_enabled=' + event_enabled + ' prob=' + probability
         + ' vol=' + volume + ' user_lang=' + user_lang + ' lang_code=' + lang_code)
    print('|'.join([theme, enabled, event_enabled, probability, volume, lang_code]))
except Exception:
    import traceback
    _dbg('outer exception: ' + traceback.format_exc())
    print('warcraft3|true|true|1.0|20|')
PYEOF
)
IFS='|' read -r THEME ENABLED EVENT_ENABLED PROBABILITY VOLUME LANG_CODE \
  <<< "${_config_out:-warcraft3|true|true|1.0|20|}"

npc_debug "resolved: theme=$THEME enabled=$ENABLED event_enabled=$EVENT_ENABLED prob=$PROBABILITY vol=$VOLUME lang=$LANG_CODE"

# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------
[[ "$ENABLED" != "true" ]] && { npc_debug "gate: disabled"; exit 0; }
[[ "$EVENT_ENABLED" != "true" ]] && { npc_debug "gate: event disabled"; exit 0; }
# Empty LANG_CODE means the theme is missing, malformed, or declared no usable language.
[[ -z "$LANG_CODE" ]] && { npc_debug "gate: empty LANG_CODE"; exit 0; }

# Probability roll — single awk handles both the roll and the play/skip decision.
PROB_CHECK=$(awk -v seed="$(( $$ * 32768 + RANDOM ))" -v p="$PROBABILITY" \
  'BEGIN{srand(seed); print (rand() <= p) ? "play" : "skip"}')
[[ "$PROB_CHECK" != "play" ]] && { npc_debug "gate: probability skip (p=$PROBABILITY)"; exit 0; }

# ---------------------------------------------------------------------------
# Resolve clip directory and play
# ---------------------------------------------------------------------------
CLIP_DIR="${PLUGIN_ROOT}/sounds/${THEME}/${LANG_CODE}/${EVENT}"
[[ ! -d "$CLIP_DIR" ]] && { npc_debug "gate: no clip dir ($CLIP_DIR)"; exit 0; }

CLIPS=()
for f in "$CLIP_DIR"/*.mp3; do
  [[ -f "$f" ]] && CLIPS+=("$f")
done
[[ ${#CLIPS[@]} -eq 0 ]] && { npc_debug "gate: clip dir empty ($CLIP_DIR)"; exit 0; }

CLIP="${CLIPS[RANDOM % ${#CLIPS[@]}]}"
read -r VOLUME_FLOAT VOLUME_SCALE < <(awk -v v="$VOLUME" 'BEGIN{printf "%.2f %d\n", v/100, v*327}')
npc_debug "playing: $CLIP"

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
