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

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/npc.py" lang <code|auto>
```

- If output is `done` and arg was `auto`: confirm `Language set to auto-detect.`
- If output is `done` and arg was a code: confirm `Language set to <code>.`

Note: the plugin does not validate the code against the active theme. If the theme
does not support `<code>`, it falls back to the theme's `defaultLanguage` at runtime.
