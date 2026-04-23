---
name: volume
description: Set npc playback volume from 0 to 100. Invoke as /npc:volume <N>.
---

# /npc:volume — set playback volume

Validate that the argument is an integer 0–100. If missing or out of range, print:
`Volume must be between 0 and 100.` and stop.

```bash
python3 -c "
import json, os
cfg_path = os.environ.get('NPC_CONFIG', os.path.expanduser('~/.claude/npc.json'))
try:
    with open(cfg_path) as f: c = json.load(f)
except Exception: c = {}
c['volume'] = <N>
os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
with open(cfg_path, 'w') as f: json.dump(c, f, indent=2)
print('done')
"
```

Confirm: `Volume set to <N>%.`
