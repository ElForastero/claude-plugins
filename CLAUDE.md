# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

This is a **Claude Code plugin marketplace** — a monorepo where each plugin is a self-contained directory under `plugins/`. `.claude-plugin/marketplace.json` at the root is the marketplace manifest Claude Code reads when users run `/plugin marketplace add ElForastero/claude-plugins`. Adding a plugin requires both a new directory and a new entry in `.claude-plugin/marketplace.json`.

There is no build system, no package manager, no test runner. Everything is shell + Python-via-heredoc, invoked by Claude Code's hook system at runtime on the end user's machine.

## Plugin layout (contract Claude Code enforces)

Every plugin under `plugins/<name>/` must have:

- `.claude-plugin/plugin.json` — manifest (name, version, description, author). The `name` here must match the directory name and the `.claude-plugin/marketplace.json` entry.
- `hooks/hooks.json` — declares hook handlers. Commands reference `${CLAUDE_PLUGIN_ROOT}` (Claude Code injects this; do not hardcode paths).
- `skills/<name>/SKILL.md` — slash commands. Frontmatter `name:` becomes `/plugin-name:skill-name`. The body is prompt content Claude executes when the skill is invoked. Each skill must be a subdirectory named after the skill, containing a file named exactly `SKILL.md`.

## npc plugin architecture

The npc plugin (`plugins/npc/`) plays audio clips on Claude Code lifecycle events. Three coordinating layers:

1. **Hook wiring** (`hooks/hooks.json`) — maps each lifecycle event (`SessionStart`, `UserPromptSubmit`, `Stop`, `PreCompact`, etc.) to `bash play.sh <EventName>`. All hooks use `"async": true` so playback never blocks Claude. Note `Stop` reuses `TaskCompleted` clips by design.

2. **Playback dispatcher** (`hooks/play.sh`) — bash wrapper that:
   - Reads `~/.claude/npc.json` (user config) via an inline `python3` heredoc. Python is used here because it owns the language-detection subprocess (shells out to `detect-lang.sh` only when needed) and tolerates missing/malformed JSON.
   - Gates on `enabled`, per-event toggle, and a probability roll (`awk rand()`).
   - Resolves clip dir to `sounds/<theme>/<lang>/<Event>/`, picks a random `.mp3`, and plays via the first available audio player: `afplay` → `mpg123` → `ffplay` → `mplayer` → `cvlc` → `powershell.exe`.
   - **Must always `exit 0`** — a broken hook must never interrupt Claude Code. Preserve this invariant when editing.

3. **User-facing control** (`skills/`) — four slash commands, each a subdirectory containing `SKILL.md`: `/npc:toggle` (flip enabled), `/npc:volume` (set 0–100), `/npc:lang` (set ISO code or `auto`), `/npc:status` (read-only display). Each skill is a markdown prompt telling Claude how to parse args and mutate `~/.claude/npc.json` via inline `python3 -c` snippets. Config writes go through Python (not `jq`) because Python is guaranteed on macOS/Linux and gracefully handles a missing file.

## Theme packs (drop-in content)

Themes live under `plugins/npc/sounds/<theme>/` with this shape:

```
sounds/<theme>/
├── theme.json          # { name, description, languages: [...], defaultLanguage, credits }
└── <lang>/             # one dir per 2-letter ISO code listed in languages[]
    └── <EventName>/    # e.g. SessionStart/, TaskCompleted/
        └── *.mp3
```

Language resolution order in `play.sh`: explicit config `language` → system detect (`detect-lang.sh`) → theme `defaultLanguage`. If the resolved code isn't in the theme's `languages[]`, falls back to `defaultLanguage`. A missing event folder is silently skipped (not an error).

The bundled `warcraft3` theme currently ships only `ru/`. Adding an `en/` pack is a content-only change — no code edits.

## Commit conventions

Recent history uses Conventional Commits (`feat:`, `fix:`, etc.). Follow that style.

## Testing a hook change locally

No test suite exists. To exercise `play.sh` without reinstalling the plugin into Claude Code, invoke it directly with a scratch config:

```bash
echo '{"theme":"warcraft3","enabled":true,"volume":30,"events":{"SessionStart":true}}' > /tmp/npc-test.json
NPC_CONFIG=/tmp/npc-test.json \
  CLAUDE_PLUGIN_ROOT="$PWD/plugins/npc" \
  bash plugins/npc/hooks/play.sh SessionStart
```

A clip should play. If not, re-run with `set -x` prepended to `play.sh` or drop the `2>/dev/null` on the Python heredoc to surface errors.

## Validating manifests

Both `plugin.json` and `marketplace.json` are schema-validated by Claude Code at install time. Run the official validator locally before opening a PR:

```bash
bash scripts/validate-manifests.sh
```

This calls `claude plugin validate` against the root marketplace and every `plugins/*/` directory. The same script runs on every PR via `.github/workflows/validate-manifests.yml`. Field-type errors (e.g. `repository` must be a string) and unknown root-level keys are both caught — the validator is strict, so don't add fields that aren't in the documented schema.

## When editing, keep in mind

- Bumping a plugin's version: update both `plugins/<name>/.claude-plugin/plugin.json` and the matching entry in the root `.claude-plugin/marketplace.json`.
- `hooks/play.sh` runs on every lifecycle event — keep it fast and silent on failure. `2>/dev/null` and `|| true`-style fallbacks are intentional, not sloppy.
- The `python3` heredocs in `play.sh` and `skills/npc.md` exist specifically to avoid a JSON parser dependency (`jq`) that isn't universally installed. Don't "clean them up" into `jq`.
- `$CLAUDE_PLUGIN_ROOT` is only set when Claude Code invokes a hook. Scripts fall back to deriving it from `$BASH_SOURCE` so they can also be tested standalone.
