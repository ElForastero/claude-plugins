---
name: lang
description: Set npc language (2-letter ISO 639-1 code) or reset to auto-detect. Invoke as /npc:lang <code|auto>.
---

# /npc:lang — set preferred language

Read the argument:

- **`auto`** → remove the `language` key so the plugin auto-detects from system preferences on each event
- **`<code>`** where `<code>` is a 2-letter lowercase ISO 639-1 code (e.g. `en`, `ru`) → set language
- **Anything else** → print `Language must be a 2-letter ISO code (e.g., en, ru).` and stop

Validate `<code>` against `^[a-z]{2}$`. If invalid, print:
`Language must be a 2-letter ISO code (e.g., en, ru).` and stop.

## Set language (`lang <code>`)

```bash
python3 -c "
import json, os
cfg_path = os.environ.get('NPC_CONFIG', os.path.expanduser('~/.claude/npc.json'))
try:
    with open(cfg_path) as f: c = json.load(f)
except Exception: c = {}
c['language'] = '<code>'
os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
with open(cfg_path, 'w') as f: json.dump(c, f, indent=2)
print('done')
"
```

Confirm: `Language set to <code>.`

Note: the plugin does not validate the code against the active theme. If the theme
does not support `<code>`, it falls back to the theme's `defaultLanguage` at runtime.

## Reset language (`lang auto`)

```bash
python3 -c "
import json, os
cfg_path = os.environ.get('NPC_CONFIG', os.path.expanduser('~/.claude/npc.json'))
try:
    with open(cfg_path) as f: c = json.load(f)
except Exception: c = {}
c.pop('language', None)
os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
with open(cfg_path, 'w') as f: json.dump(c, f, indent=2)
print('done')
"
```

Confirm: `Language set to auto-detect.`
