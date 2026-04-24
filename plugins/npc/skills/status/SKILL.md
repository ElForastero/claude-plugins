---
name: status
description: "Show current npc status: on/off, theme, language, volume. Invoke as /npc:status."
---

# /npc:status — show current configuration

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/npc.py" status
```

The command outputs a JSON object with these fields:
- `enabled` — bool
- `theme` — string
- `volume` — integer
- `language` — string or null (null means auto-detect)
- `detected_lang` — string or null (system language detected when `language` is null)

## Print status

Output one line:

```
NPC: ON | Theme: warcraft3 | Lang: en | Volume: 50%
```

- When `language` is explicitly set, show it verbatim: `Lang: en`
- When `language` is null, show `Lang: auto (<detected_lang>)` — e.g. `Lang: auto (en)`. If `detected_lang` is also null, show `Lang: auto`

Do not write to the file.
