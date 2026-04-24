---
name: volume
description: Set npc playback volume from 0 to 100. Invoke as /npc:volume <N>.
---

# /npc:volume — set playback volume

Validate that the argument is an integer 0–100. If missing or out of range, print:
`Volume must be between 0 and 100.` and stop.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/npc.py" volume <N>
```

Confirm: `Volume set to <N>%.`
