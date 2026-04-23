---
name: toggle
description: Toggle npc sounds on or off. Invoke as /npc:toggle.
---

# /npc:toggle — flip enabled state

Flip the `enabled` flag in `~/.claude/npc.json` (override via `$NPC_CONFIG`).

```bash
python3 -c "
import json, os
cfg_path = os.environ.get('NPC_CONFIG', os.path.expanduser('~/.claude/npc.json'))
try:
    with open(cfg_path) as f: c = json.load(f)
except Exception: c = {}
c['enabled'] = not c.get('enabled', True)
os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
with open(cfg_path, 'w') as f: json.dump(c, f, indent=2)
print('enabled' if c['enabled'] else 'disabled')
"
```

Print the resulting state: `NPC enabled.` or `NPC disabled.`
