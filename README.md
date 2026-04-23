# Claude Code Plugins Marketplace

A monorepo of plugins for [Claude Code](https://claude.ai/code). Each plugin lives in its own directory under `plugins/` and can be installed independently.

## Plugins

| Name | Description | Tags |
|------|-------------|------|
| [npc](plugins/npc) | Plays NPC voice clips from games and movies on Claude Code lifecycle events | audio, fun, hooks |

## Installing a Plugin

### 1. Add this marketplace to Claude Code

Inside any Claude Code session, run:

```
/plugin marketplace add ElForastero/claude-plugins
```

This registers the marketplace once — you won't need to repeat it.

### 2. Install a plugin

```
/plugin install npc@ElForastero-claude-plugins
```

Or open the interactive plugin manager with `/plugin` and browse the **Discover** tab.

### 3. Follow plugin-specific setup (if any)

Some plugins need extra steps after installation — for example, installing a system dependency or copying a config file. Check the plugin's own `README.md` for details.

## How Plugins Work

Each plugin can ship any combination of:

- **Hooks** — shell commands that run automatically on Claude Code lifecycle events (session start, prompt submit, task complete, etc.)
- **Skills** — slash commands available inside Claude Code sessions (e.g. `/npc:npc`)

Plugin hooks and skills are registered automatically on install.

## Contributing

Add your plugin as a new directory under `plugins/<plugin-name>/` with a `.claude-plugin/plugin.json` manifest, then open a PR and update `registry.json`.
