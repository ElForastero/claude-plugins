#!/usr/bin/env python3
"""npc — NPC voice clip playback for Claude Code lifecycle events.

CLI:
  npc.py play <EventName>
  npc.py toggle
  npc.py volume <0-100>
  npc.py lang <code|auto>
  npc.py status
"""
import json
import os
import random
import shutil
import subprocess
import sys
import traceback
from pathlib import Path

_HERE = Path(__file__).resolve().parent
PLUGIN_ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", str(_HERE.parent)))
CONFIG_PATH = Path(os.environ.get("NPC_CONFIG", Path.home() / ".claude" / "npc.json"))
_DEBUG = os.environ.get("NPC_DEBUG") == "1"
_DEBUG_LOG = Path(os.environ.get("TMPDIR", "/tmp")) / "npc-debug.log"


def _dbg(msg: str) -> None:
    if not _DEBUG:
        return
    try:
        with _DEBUG_LOG.open("a") as fh:
            fh.write(f"[npc.py] {msg}\n")
    except Exception:
        pass


def _truthy(v, default=True) -> bool:
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    if isinstance(v, str):
        return v.strip().lower() not in ("", "false", "0", "no", "off")
    return bool(v)


def _as_str(v, default: str) -> str:
    if v is None or (isinstance(v, str) and not v.strip()):
        return default
    return str(v)


def _as_int(v, default: int) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _as_float(v, default: float) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _as_dict(v) -> dict:
    return v if isinstance(v, dict) else {}


def _as_list(v) -> list:
    return v if isinstance(v, list) else []


def _load_config() -> dict:
    try:
        with CONFIG_PATH.open() as f:
            c = json.load(f)
        if not isinstance(c, dict):
            _dbg("config is not a JSON object, ignoring")
            return {}
        return c
    except FileNotFoundError:
        return {}
    except Exception as e:
        _dbg(f"config unreadable: {e!r}")
        return {}


def _save_config(c: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w") as f:
        json.dump(c, f, indent=2)


def _effective_user_lang(c: dict):
    lang = c.get("language")
    if not isinstance(lang, str) or lang.strip().lower() in ("", "auto"):
        return None
    return lang.lower()


def _detect_system_lang() -> str:
    try:
        if sys.platform == "darwin":
            r = subprocess.run(
                ["defaults", "read", "-g", "AppleLanguages"],
                capture_output=True, text=True, timeout=2,
            )
            for token in r.stdout.split():
                token = token.strip('",()').split("-")[0].split("_")[0]
                if len(token) == 2 and token.isalpha():
                    return token.lower()
        elif sys.platform == "win32":
            r = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command",
                 "(Get-Culture).TwoLetterISOLanguageName"],
                capture_output=True, text=True, timeout=2,
            )
            code = r.stdout.strip().lower()
            if len(code) == 2 and code.isalpha():
                return code
        else:
            for var in ("LC_ALL", "LC_MESSAGES", "LANG"):
                val = os.environ.get(var, "")
                code = val.split(".")[0].split("_")[0].lower()
                if len(code) == 2 and code.isalpha():
                    return code
    except Exception as e:
        _dbg(f"detect_system_lang failed: {e!r}")
    return ""


def _resolve(event: str) -> dict:
    try:
        c = _load_config()

        theme = _as_str(c.get("theme"), "warcraft3")
        enabled = _truthy(c.get("enabled"), True)
        if not enabled:
            return {
                "theme": theme, "enabled": False, "event_enabled": False,
                "probability": 1.0, "volume": 20, "lang_code": "", "detected_lang": "",
            }

        event_enabled = _truthy(_as_dict(c.get("events")).get(event), True)
        if not event_enabled:
            return {
                "theme": theme, "enabled": True, "event_enabled": False,
                "probability": 1.0, "volume": 20, "lang_code": "", "detected_lang": "",
            }

        probability = _as_float(_as_dict(c.get("probability")).get(event), 1.0)
        volume = _as_int(c.get("volume"), 20)

        user_lang = _effective_user_lang(c)
        detected_lang = ""
        if user_lang is None:
            detected_lang = _detect_system_lang()
            effective_lang = detected_lang
        else:
            effective_lang = user_lang

        lang_code = ""
        theme_json = PLUGIN_ROOT / "sounds" / theme / "theme.json"
        try:
            with theme_json.open() as f:
                tm = json.load(f)
            languages = [str(l).lower() for l in _as_list(tm.get("languages")) if l]
            default_lang = _as_str(tm.get("defaultLanguage"), "").lower()
            fallback = default_lang if default_lang in languages else (languages[0] if languages else "")
            if fallback:
                lang_code = effective_lang if effective_lang in languages else fallback
        except Exception as e:
            _dbg(f"theme.json read failed ({theme_json}): {e!r}")

        _dbg(
            f"resolved theme={theme} enabled={enabled} event_enabled={event_enabled} "
            f"prob={probability} vol={volume} lang_code={lang_code}"
        )
        return {
            "theme": theme,
            "enabled": True,
            "event_enabled": True,
            "probability": probability,
            "volume": volume,
            "lang_code": lang_code,
            "detected_lang": detected_lang,
        }
    except Exception:
        _dbg("_resolve exception: " + traceback.format_exc())
        return {
            "theme": "warcraft3", "enabled": True, "event_enabled": True,
            "probability": 1.0, "volume": 20, "lang_code": "", "detected_lang": "",
        }


def _play_clip(path: Path, volume: int) -> None:
    volume_float = volume / 100
    volume_scale = volume * 327

    players = [
        ["afplay",         "-v", f"{volume_float:.2f}", str(path)],
        ["mpg123",         "-q", "--scale", str(volume_scale), str(path)],
        ["ffplay",         "-nodisp", "-autoexit", "-loglevel", "quiet",
                           "-af", f"volume={volume_float:.2f}", str(path)],
        ["mplayer",        "-really-quiet", "-volume", str(volume), str(path)],
        ["cvlc",           "--play-and-exit", "--gain", f"{volume_float:.2f}", str(path)],
        ["powershell.exe", "-NoProfile", "-Command",
                           "(New-Object Media.SoundPlayer $args[0]).PlaySync()",
                           str(path)],
    ]

    for cmd in players:
        if shutil.which(cmd[0]):
            try:
                subprocess.Popen(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    close_fds=True,
                )
            except Exception as e:
                _dbg(f"player {cmd[0]} failed: {e!r}")
            return


def cmd_play(event: str) -> None:
    try:
        r = _resolve(event)
        if not r["enabled"]:
            _dbg("gate: disabled")
            return
        if not r["event_enabled"]:
            _dbg("gate: event disabled")
            return
        if not r["lang_code"]:
            _dbg("gate: empty lang_code")
            return
        if random.random() >= r["probability"]:
            _dbg(f"gate: probability skip (p={r['probability']})")
            return

        clip_dir = PLUGIN_ROOT / "sounds" / r["theme"] / r["lang_code"] / event
        if not clip_dir.is_dir():
            _dbg(f"gate: no clip dir ({clip_dir})")
            return
        clips = list(clip_dir.glob("*.mp3"))
        if not clips:
            _dbg(f"gate: clip dir empty ({clip_dir})")
            return

        clip = random.choice(clips)
        _dbg(f"playing: {clip}")
        _play_clip(clip, r["volume"])
    except Exception:
        _dbg("cmd_play exception: " + traceback.format_exc())


def cmd_toggle() -> None:
    c = _load_config()
    c["enabled"] = not _truthy(c.get("enabled"), True)
    _save_config(c)
    print("enabled" if c["enabled"] else "disabled")


def cmd_volume(n: int) -> None:
    c = _load_config()
    c["volume"] = n
    _save_config(c)
    print("done")


def cmd_lang(code: str) -> None:
    c = _load_config()
    if code == "auto":
        c.pop("language", None)
    else:
        c["language"] = code
    _save_config(c)
    print("done")


def cmd_status() -> None:
    c = _load_config()
    language = _effective_user_lang(c)

    detected_lang = None
    if language is None:
        detected = _detect_system_lang()
        detected_lang = detected if detected else None

    print(json.dumps({
        "enabled": _truthy(c.get("enabled"), True),
        "theme": _as_str(c.get("theme"), "warcraft3"),
        "volume": _as_int(c.get("volume"), 20),
        "language": language,
        "detected_lang": detected_lang,
    }))


def main() -> None:
    args = sys.argv[1:]
    if not args:
        return

    cmd = args[0]

    if cmd == "play":
        event = args[1] if len(args) > 1 else ""
        if event:
            cmd_play(event)

    elif cmd == "toggle":
        cmd_toggle()

    elif cmd == "volume":
        try:
            n = int(args[1])
            if not 0 <= n <= 100:
                raise ValueError
            cmd_volume(n)
        except (IndexError, ValueError):
            print("Volume must be between 0 and 100.")

    elif cmd == "lang":
        if len(args) < 2:
            print("Language must be a 2-letter ISO code (e.g., en, ru).")
            return
        code = args[1]
        if code != "auto" and not (len(code) == 2 and code.isalpha()):
            print("Language must be a 2-letter ISO code (e.g., en, ru).")
            return
        cmd_lang(code.lower())

    elif cmd == "status":
        cmd_status()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
