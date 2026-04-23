# npc

Plays random NPC voice clips from games and movies at key moments in your Claude Code workflow — session start, prompt submit, task complete, and more. Ships with a Warcraft III (Russian) theme. Add more themes by dropping a folder.

## Install

**Prerequisite:** An audio player must be available — `afplay` (macOS, built-in), `mpg123` or `ffplay` (Linux), or PowerShell (Windows, built-in).

Inside any Claude Code session:

```
/plugin install npc@ElForastero-claude-plugins
```

That's it. Hooks are wired automatically.

## Usage

Control npc from inside any Claude Code session:

```
/npc:status           — show current status (enabled, theme, language, volume)
/npc:toggle           — toggle sound on/off
/npc:volume 70        — set volume to 70%
/npc:lang en          — set preferred language (2-letter ISO code)
/npc:lang auto        — auto-detect language from system preferences
```

Changes take effect immediately on the next event — no restart needed.

## Configuration

Config is read from `~/.claude/npc.json`. Create the file to customize behavior:

```json
{
  "theme": "warcraft3",
  "language": "auto",
  "enabled": true,
  "volume": 50,
  "events": {
    "SessionStart": true,
    "UserPromptSubmit": true,
    "SubagentStart": true,
    "TaskCompleted": true,
    "PreCompact": true,
    "StopFailure": true,
    "Elicitation": true
  },
  "probability": {
    "Elicitation": 0.3
  }
}
```

Override the config path via the `NPC_CONFIG` environment variable.

### Options

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `theme` | string | `"warcraft3"` | Active theme folder under `sounds/` |
| `language` | string | `"auto"` | 2-letter ISO 639-1 code (e.g. `"en"`, `"ru"`). `"auto"` detects from system. |
| `enabled` | boolean | `true` | Global kill switch |
| `volume` | integer 0–100 | `50` | Playback volume percentage |
| `events.<Name>` | boolean | `true` | Per-event toggle — omit events you want enabled |
| `probability.<Name>` | float 0.0–1.0 | `1.0` | Chance of playing a clip when the event fires |

### Language Selection

Themes can ship clips in multiple languages. The resolution order is:

1. If `language` is a 2-letter ISO code (e.g. `"en"`), use it.
2. If `language` is `"auto"`, `null`, or missing, detect from system preferences:
   - **macOS**: `defaults read -g AppleLanguages`
   - **Linux**: `$LC_ALL` / `$LANG`
   - **Windows**: `(Get-Culture).TwoLetterISOLanguageName`
3. If the resolved code is not in the active theme's `languages` array, fall back to the theme's `defaultLanguage`.

The bundled `warcraft3` theme only ships Russian (`ru`) clips, so any other preference falls back to Russian until an English pack is added.

### Stop vs. TaskCompleted

`Stop` reuses clips from `TaskCompleted/` by default. To give session-end its own sound, add a `Stop/` folder to your theme with custom clips.

## Supported Events

| Event | When it fires |
|-------|--------------|
| `SessionStart` | New Claude Code session starts |
| `UserPromptSubmit` | User submits a prompt |
| `SubagentStart` | A subagent begins |
| `TaskCompleted` | A task is marked complete |
| `Stop` | Session ends normally (reuses TaskCompleted sounds by default) |
| `PreCompact` | Context window auto-compact triggers |
| `StopFailure` | Session ends with failure |
| `Elicitation` | Claude asks the user a question |

## Adding a New Theme

### 1. Create theme metadata

Create `sounds/<theme-name>/theme.json`:

```json
{
  "name": "Theme Display Name",
  "description": "Brief description",
  "languages": ["en", "ru"],
  "defaultLanguage": "en",
  "credits": "Content creator — source"
}
```

- `languages` — non-empty array of 2-letter ISO 639-1 codes that the theme ships clips for.
- `defaultLanguage` — must be one of `languages`; used when the user's preferred language is unavailable.

### 2. Add event directories and clips

Clips live under a per-language subdirectory:

```
sounds/<theme-name>/
├── theme.json
├── en/
│   ├── SessionStart/
│   │   ├── clip1.mp3
│   │   └── clip2.mp3
│   ├── UserPromptSubmit/
│   │   └── clip1.mp3
│   └── TaskCompleted/
│       └── clip1.mp3
└── ru/
    └── SessionStart/
        └── clip1.mp3
```

Missing event folders are silently skipped. Every entry in `languages` should have a matching subdirectory.

### 3. Activate the theme

Update `~/.claude/npc.json`:

```json
{ "theme": "<theme-name>" }
```

No code changes or restarts needed.

## Cross-Platform Audio Support

The plugin detects available audio players in this order:

| Player | Platform |
|--------|----------|
| `afplay` | macOS (built-in) |
| `mpg123` | Linux — `brew install mpg123` / `apt install mpg123` |
| `ffplay` | Linux/macOS — part of ffmpeg |
| `mplayer` | Linux/macOS |
| `cvlc` | VLC, all platforms |
| `powershell` | Windows (built-in — volume control not supported) |

## License

See [LICENSE](LICENSE) for details.
