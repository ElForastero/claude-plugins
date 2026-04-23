---
name: status
description: "Show current npc status: on/off, theme, language, volume. Invoke as /npc:status."
---

# /npc:status — show current configuration

Read the config (handles missing file gracefully):

```bash
python3 -c "
import json, os
cfg_path = os.environ.get('NPC_CONFIG', os.path.expanduser('~/.claude/npc.json'))
try:
    with open(cfg_path) as f:
        c = json.load(f)
except Exception:
    c = {}
print(json.dumps({
    'enabled': c.get('enabled', True),
    'theme': c.get('theme', 'warcraft3'),
    'volume': c.get('volume', 50),
    'language': c.get('language', None),
}))
"
```

## Detect system language (when language is unset)

If `language` is absent or `"auto"`, detect the system language:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/hooks/detect-lang.sh"
```

## Print status

Output one line:

```
NPC: ON | Theme: warcraft3 | Lang: en | Volume: 50%
```

- When `language` is explicitly set, show it verbatim: `Lang: en`
- When `language` is unset or `"auto"`, show `Lang: auto (<detected>)` — e.g. `Lang: auto (en)`. If detection also returns empty, show `Lang: auto`

Do not write to the file.
