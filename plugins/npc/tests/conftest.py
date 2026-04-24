import json
import sys
from pathlib import Path

import pytest

# npc.py lives in hooks/, not tests/
# The bare `try: main()` at the bottom of npc.py runs on import but is safe —
# main() returns immediately when sys.argv[1:] contains only pytest flags/paths.
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))
import npc  # noqa: E402


@pytest.fixture
def tmp_config(tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    monkeypatch.setattr(npc, "CONFIG_PATH", cfg)
    return cfg


@pytest.fixture
def fake_plugin_root(tmp_path, monkeypatch):
    root = tmp_path / "plugin_root"
    sounds = root / "sounds" / "warcraft3"
    sounds.mkdir(parents=True)
    (sounds / "theme.json").write_text(
        json.dumps({"languages": ["ru"], "defaultLanguage": "ru"})
    )
    clip_dir = sounds / "ru" / "UserPromptSubmit"
    clip_dir.mkdir(parents=True)
    (clip_dir / "da.mp3").write_bytes(b"")
    monkeypatch.setattr(npc, "PLUGIN_ROOT", root)
    return root
