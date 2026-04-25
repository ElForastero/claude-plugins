---
name: toggle
description: Toggle npc sounds on or off. Invoke as /npc:toggle.
---

# /npc:toggle — flip enabled state

Flip the `enabled` flag in `~/.claude/npc.json` (override via `$NPC_CONFIG`).

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/npc.py" toggle
```

Print the resulting state: `NPC enabled.` or `NPC disabled.`
