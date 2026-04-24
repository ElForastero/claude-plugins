import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import npc


class TestTruthy:
    def test_none_returns_default_true(self):
        assert npc._truthy(None) is True

    def test_none_with_false_default(self):
        assert npc._truthy(None, default=False) is False

    def test_bool_true_passthrough(self):
        assert npc._truthy(True) is True

    def test_bool_false_passthrough(self):
        assert npc._truthy(False) is False

    def test_int_zero_is_falsy(self):
        assert npc._truthy(0) is False

    def test_int_nonzero_is_truthy(self):
        assert npc._truthy(1) is True

    def test_float_zero_is_falsy(self):
        assert npc._truthy(0.0) is False

    def test_float_nonzero_is_truthy(self):
        assert npc._truthy(0.1) is True

    @pytest.mark.parametrize("s", ["false", "False", "FALSE", "0", "no", "No", "off", "Off", ""])
    def test_string_falsy_literals(self, s):
        assert npc._truthy(s) is False

    def test_string_whitespace_only_is_falsy(self):
        assert npc._truthy("   ") is False

    @pytest.mark.parametrize("s", ["true", "True", "yes", "1", "on", "anything"])
    def test_string_truthy_values(self, s):
        assert npc._truthy(s) is True

    def test_empty_list_is_falsy(self):
        assert npc._truthy([]) is False

    def test_nonempty_list_is_truthy(self):
        assert npc._truthy([1]) is True


class TestAsStr:
    def test_none_returns_default(self):
        assert npc._as_str(None, "x") == "x"

    def test_empty_string_returns_default(self):
        assert npc._as_str("", "x") == "x"

    def test_whitespace_only_returns_default(self):
        assert npc._as_str("   ", "x") == "x"

    def test_int_becomes_string(self):
        assert npc._as_str(42, "x") == "42"

    def test_normal_string_returned(self):
        assert npc._as_str("hello", "x") == "hello"


class TestAsInt:
    def test_none_returns_default(self):
        assert npc._as_int(None, 5) == 5

    def test_int_returned_as_is(self):
        assert npc._as_int(7, 0) == 7

    def test_float_string_returns_default(self):
        assert npc._as_int("3.7", 99) == 99

    def test_valid_int_string(self):
        assert npc._as_int("42", 0) == 42

    def test_garbage_string_returns_default(self):
        assert npc._as_int("abc", 0) == 0

    def test_bool_true_becomes_1(self):
        assert npc._as_int(True, 0) == 1


class TestAsFloat:
    def test_none_returns_default(self):
        assert npc._as_float(None, 0.5) == 0.5

    def test_float_string_parsed(self):
        assert npc._as_float("3.14", 0.0) == pytest.approx(3.14)

    def test_int_converted(self):
        assert npc._as_float(5, 0.0) == 5.0

    def test_garbage_returns_default(self):
        assert npc._as_float("abc", 0.5) == 0.5


class TestAsContainers:
    def test_as_dict_returns_dict_unchanged(self):
        d = {"a": 1}
        assert npc._as_dict(d) is d

    @pytest.mark.parametrize("v", [None, [], "foo", 42])
    def test_as_dict_non_dict_returns_empty(self, v):
        assert npc._as_dict(v) == {}

    def test_as_list_returns_list_unchanged(self):
        lst = [1, 2]
        assert npc._as_list(lst) is lst

    @pytest.mark.parametrize("v", [None, {}, "foo", 42])
    def test_as_list_non_list_returns_empty(self, v):
        assert npc._as_list(v) == []


class TestEffectiveUserLang:
    def test_no_language_key_returns_none(self):
        assert npc._effective_user_lang({}) is None

    def test_auto_returns_none(self):
        assert npc._effective_user_lang({"language": "auto"}) is None

    def test_auto_case_insensitive(self):
        assert npc._effective_user_lang({"language": "AUTO"}) is None

    def test_empty_string_returns_none(self):
        assert npc._effective_user_lang({"language": ""}) is None

    def test_whitespace_returns_none(self):
        assert npc._effective_user_lang({"language": "  "}) is None

    def test_non_string_returns_none(self):
        assert npc._effective_user_lang({"language": 42}) is None

    def test_valid_code_lowercased(self):
        assert npc._effective_user_lang({"language": "RU"}) == "ru"

    def test_two_letter_code(self):
        assert npc._effective_user_lang({"language": "en"}) == "en"


class TestLoadConfig:
    def test_missing_file_returns_empty_dict(self, tmp_config):
        assert npc._load_config() == {}

    def test_valid_json_object_returned(self, tmp_config):
        tmp_config.write_text('{"enabled": true, "volume": 50}')
        assert npc._load_config() == {"enabled": True, "volume": 50}

    def test_json_array_at_root_returns_empty_dict(self, tmp_config):
        tmp_config.write_text('[1, 2, 3]')
        assert npc._load_config() == {}

    def test_malformed_json_returns_empty_dict(self, tmp_config):
        tmp_config.write_text('not json at all')
        assert npc._load_config() == {}

    def test_empty_file_returns_empty_dict(self, tmp_config):
        tmp_config.write_text('')
        assert npc._load_config() == {}


class TestSaveConfig:
    def test_creates_parent_dirs(self, tmp_path, monkeypatch):
        deep = tmp_path / "a" / "b" / "c" / "config.json"
        monkeypatch.setattr(npc, "CONFIG_PATH", deep)
        npc._save_config({"x": 1})
        assert deep.exists()

    def test_written_json_round_trips(self, tmp_config):
        data = {"enabled": False, "volume": 75, "language": "ru"}
        npc._save_config(data)
        assert json.loads(tmp_config.read_text()) == data

    def test_overwrites_existing_config(self, tmp_config):
        tmp_config.write_text('{"old": true}')
        npc._save_config({"new": 1})
        assert json.loads(tmp_config.read_text()) == {"new": 1}

    def test_save_and_load_round_trip(self, tmp_config):
        data = {"enabled": True, "volume": 30}
        npc._save_config(data)
        assert npc._load_config() == data


class TestDetectSystemLang:
    def test_darwin_returns_first_valid_token(self, monkeypatch):
        monkeypatch.setattr(npc.sys, "platform", "darwin")
        monkeypatch.setattr(
            npc.subprocess, "run",
            MagicMock(return_value=MagicMock(stdout='(\n"en-US",\n"ru-RU"\n)')),
        )
        assert npc._detect_system_lang() == "en"

    def test_darwin_strips_region_code(self, monkeypatch):
        monkeypatch.setattr(npc.sys, "platform", "darwin")
        monkeypatch.setattr(
            npc.subprocess, "run",
            MagicMock(return_value=MagicMock(stdout='(\n"zh-Hans-CN"\n)')),
        )
        assert npc._detect_system_lang() == "zh"

    def test_darwin_empty_output_returns_empty_string(self, monkeypatch):
        monkeypatch.setattr(npc.sys, "platform", "darwin")
        monkeypatch.setattr(
            npc.subprocess, "run",
            MagicMock(return_value=MagicMock(stdout="")),
        )
        assert npc._detect_system_lang() == ""

    def test_darwin_subprocess_exception_returns_empty_string(self, monkeypatch):
        monkeypatch.setattr(npc.sys, "platform", "darwin")
        monkeypatch.setattr(
            npc.subprocess, "run",
            MagicMock(side_effect=Exception("timeout")),
        )
        assert npc._detect_system_lang() == ""

    def test_linux_reads_lc_all(self, monkeypatch):
        monkeypatch.setattr(npc.sys, "platform", "linux")
        monkeypatch.setenv("LC_ALL", "fr_FR.UTF-8")
        monkeypatch.delenv("LC_MESSAGES", raising=False)
        monkeypatch.delenv("LANG", raising=False)
        assert npc._detect_system_lang() == "fr"

    def test_linux_skips_lc_all_falls_through_to_lang(self, monkeypatch):
        monkeypatch.setattr(npc.sys, "platform", "linux")
        monkeypatch.delenv("LC_ALL", raising=False)
        monkeypatch.delenv("LC_MESSAGES", raising=False)
        monkeypatch.setenv("LANG", "de_DE.UTF-8")
        assert npc._detect_system_lang() == "de"

    def test_linux_no_env_vars_returns_empty(self, monkeypatch):
        monkeypatch.setattr(npc.sys, "platform", "linux")
        monkeypatch.delenv("LC_ALL", raising=False)
        monkeypatch.delenv("LC_MESSAGES", raising=False)
        monkeypatch.delenv("LANG", raising=False)
        assert npc._detect_system_lang() == ""

    def test_linux_underscore_separator(self, monkeypatch):
        monkeypatch.setattr(npc.sys, "platform", "linux")
        monkeypatch.setenv("LC_ALL", "pt_BR")
        monkeypatch.delenv("LC_MESSAGES", raising=False)
        monkeypatch.delenv("LANG", raising=False)
        assert npc._detect_system_lang() == "pt"

    def test_windows_returns_two_letter_code(self, monkeypatch):
        monkeypatch.setattr(npc.sys, "platform", "win32")
        monkeypatch.setattr(
            npc.subprocess, "run",
            MagicMock(return_value=MagicMock(stdout="en\n")),
        )
        assert npc._detect_system_lang() == "en"

    def test_windows_long_output_returns_empty(self, monkeypatch):
        monkeypatch.setattr(npc.sys, "platform", "win32")
        monkeypatch.setattr(
            npc.subprocess, "run",
            MagicMock(return_value=MagicMock(stdout="english\n")),
        )
        assert npc._detect_system_lang() == ""


class TestResolve:
    def test_disabled_config_returns_early(self, monkeypatch, fake_plugin_root):
        monkeypatch.setattr(npc, "_load_config", lambda: {"enabled": False})
        r = npc._resolve("UserPromptSubmit")
        assert r["enabled"] is False
        assert r["event_enabled"] is False

    def test_event_disabled_returns_early(self, monkeypatch, fake_plugin_root):
        monkeypatch.setattr(npc, "_load_config", lambda: {
            "enabled": True,
            "events": {"UserPromptSubmit": False},
        })
        r = npc._resolve("UserPromptSubmit")
        assert r["enabled"] is True
        assert r["event_enabled"] is False

    def test_explicit_lang_skips_detection(self, monkeypatch, fake_plugin_root):
        monkeypatch.setattr(npc, "_load_config", lambda: {
            "enabled": True, "language": "ru", "volume": 50,
        })
        detect_calls = []
        monkeypatch.setattr(npc, "_detect_system_lang", lambda: detect_calls.append(1) or "xx")
        r = npc._resolve("UserPromptSubmit")
        assert r["lang_code"] == "ru"
        assert r["volume"] == 50
        assert detect_calls == []

    def test_auto_lang_detected_but_unsupported_falls_back(self, monkeypatch, fake_plugin_root):
        monkeypatch.setattr(npc, "_load_config", lambda: {"enabled": True})
        monkeypatch.setattr(npc, "_detect_system_lang", lambda: "en")
        r = npc._resolve("UserPromptSubmit")
        assert r["lang_code"] == "ru"
        assert r["detected_lang"] == "en"

    def test_auto_lang_detected_and_supported(self, monkeypatch, fake_plugin_root):
        monkeypatch.setattr(npc, "_load_config", lambda: {"enabled": True})
        monkeypatch.setattr(npc, "_detect_system_lang", lambda: "ru")
        r = npc._resolve("UserPromptSubmit")
        assert r["lang_code"] == "ru"
        assert r["detected_lang"] == "ru"

    def test_per_event_probability_read(self, monkeypatch, fake_plugin_root):
        monkeypatch.setattr(npc, "_load_config", lambda: {
            "enabled": True, "language": "ru",
            "probability": {"Elicitation": 0.3},
        })
        monkeypatch.setattr(npc, "_detect_system_lang", lambda: "")
        r = npc._resolve("Elicitation")
        assert r["probability"] == pytest.approx(0.3)

    def test_missing_theme_json_yields_empty_lang_code(self, monkeypatch, tmp_path):
        empty_root = tmp_path / "empty_root"
        empty_root.mkdir()
        monkeypatch.setattr(npc, "PLUGIN_ROOT", empty_root)
        monkeypatch.setattr(npc, "_load_config", lambda: {"enabled": True, "language": "ru"})
        monkeypatch.setattr(npc, "_detect_system_lang", lambda: "")
        r = npc._resolve("UserPromptSubmit")
        assert r["lang_code"] == ""

    def test_empty_config_uses_all_defaults(self, monkeypatch, fake_plugin_root):
        monkeypatch.setattr(npc, "_load_config", lambda: {})
        monkeypatch.setattr(npc, "_detect_system_lang", lambda: "ru")
        r = npc._resolve("SessionStart")
        assert r["theme"] == "warcraft3"
        assert r["enabled"] is True
        assert r["event_enabled"] is True
        assert r["volume"] == 20
        assert r["probability"] == pytest.approx(1.0)


class TestPlayClip:
    def test_uses_first_available_player(self, monkeypatch, tmp_path):
        clip = tmp_path / "clip.mp3"
        popen_calls = []
        monkeypatch.setattr(
            npc.shutil, "which",
            lambda name: "/usr/bin/afplay" if name == "afplay" else None,
        )
        monkeypatch.setattr(
            npc.subprocess, "Popen",
            lambda cmd, **kw: popen_calls.append(cmd),
        )
        npc._play_clip(clip, 50)
        assert len(popen_calls) == 1
        assert popen_calls[0][0] == "afplay"

    def test_skips_to_next_available_player(self, monkeypatch, tmp_path):
        clip = tmp_path / "clip.mp3"
        popen_calls = []
        monkeypatch.setattr(
            npc.shutil, "which",
            lambda name: "/usr/bin/mpg123" if name == "mpg123" else None,
        )
        monkeypatch.setattr(
            npc.subprocess, "Popen",
            lambda cmd, **kw: popen_calls.append(cmd),
        )
        npc._play_clip(clip, 30)
        assert len(popen_calls) == 1
        assert popen_calls[0][0] == "mpg123"

    def test_no_player_available_does_nothing(self, monkeypatch, tmp_path):
        clip = tmp_path / "clip.mp3"
        popen_mock = MagicMock()
        monkeypatch.setattr(npc.shutil, "which", lambda name: None)
        monkeypatch.setattr(npc.subprocess, "Popen", popen_mock)
        npc._play_clip(clip, 50)
        popen_mock.assert_not_called()

    def test_afplay_volume_float_format(self, monkeypatch, tmp_path):
        clip = tmp_path / "clip.mp3"
        captured = []
        monkeypatch.setattr(
            npc.shutil, "which",
            lambda name: "/bin/afplay" if name == "afplay" else None,
        )
        monkeypatch.setattr(
            npc.subprocess, "Popen",
            lambda cmd, **kw: captured.append(cmd),
        )
        npc._play_clip(clip, 50)
        assert captured[0][2] == "0.50"

    def test_popen_exception_does_not_propagate(self, monkeypatch, tmp_path):
        clip = tmp_path / "clip.mp3"
        monkeypatch.setattr(
            npc.shutil, "which",
            lambda name: "/bin/afplay" if name == "afplay" else None,
        )
        monkeypatch.setattr(
            npc.subprocess, "Popen",
            MagicMock(side_effect=OSError("no such file")),
        )
        npc._play_clip(clip, 50)  # must not raise


class TestCmdPlay:
    def _enabled_resolve(self, **overrides):
        base = {
            "enabled": True, "event_enabled": True,
            "lang_code": "ru", "probability": 1.0,
            "volume": 50, "theme": "warcraft3",
            "detected_lang": "ru",
        }
        base.update(overrides)
        return base

    def test_gate_disabled(self, monkeypatch):
        monkeypatch.setattr(npc, "_resolve", lambda e: self._enabled_resolve(
            enabled=False, event_enabled=False,
        ))
        play_mock = MagicMock()
        monkeypatch.setattr(npc, "_play_clip", play_mock)
        npc.cmd_play("UserPromptSubmit")
        play_mock.assert_not_called()

    def test_gate_event_disabled(self, monkeypatch):
        monkeypatch.setattr(npc, "_resolve", lambda e: self._enabled_resolve(
            event_enabled=False,
        ))
        play_mock = MagicMock()
        monkeypatch.setattr(npc, "_play_clip", play_mock)
        npc.cmd_play("UserPromptSubmit")
        play_mock.assert_not_called()

    def test_gate_empty_lang_code(self, monkeypatch):
        monkeypatch.setattr(npc, "_resolve", lambda e: self._enabled_resolve(lang_code=""))
        play_mock = MagicMock()
        monkeypatch.setattr(npc, "_play_clip", play_mock)
        npc.cmd_play("UserPromptSubmit")
        play_mock.assert_not_called()

    def test_gate_probability_always_skips_at_zero(self, monkeypatch):
        # probability=0.0 → random.random() (always in [0,1)) >= 0.0 → always skip
        monkeypatch.setattr(npc, "_resolve", lambda e: self._enabled_resolve(probability=0.0))
        play_mock = MagicMock()
        monkeypatch.setattr(npc, "_play_clip", play_mock)
        npc.cmd_play("UserPromptSubmit")
        play_mock.assert_not_called()

    def test_gate_missing_clip_dir(self, monkeypatch, fake_plugin_root):
        monkeypatch.setattr(npc, "_resolve", lambda e: self._enabled_resolve())
        monkeypatch.setattr(npc.random, "random", lambda: 0.0)
        play_mock = MagicMock()
        monkeypatch.setattr(npc, "_play_clip", play_mock)
        npc.cmd_play("NonExistentEvent")
        play_mock.assert_not_called()

    def test_gate_empty_clip_dir(self, monkeypatch, fake_plugin_root):
        empty_dir = fake_plugin_root / "sounds" / "warcraft3" / "ru" / "EmptyEvent"
        empty_dir.mkdir(parents=True)
        monkeypatch.setattr(npc, "_resolve", lambda e: self._enabled_resolve())
        monkeypatch.setattr(npc.random, "random", lambda: 0.0)
        play_mock = MagicMock()
        monkeypatch.setattr(npc, "_play_clip", play_mock)
        npc.cmd_play("EmptyEvent")
        play_mock.assert_not_called()

    def test_happy_path_calls_play_clip(self, monkeypatch, fake_plugin_root):
        monkeypatch.setattr(npc, "_resolve", lambda e: self._enabled_resolve())
        monkeypatch.setattr(npc.random, "random", lambda: 0.0)
        play_mock = MagicMock()
        monkeypatch.setattr(npc, "_play_clip", play_mock)
        npc.cmd_play("UserPromptSubmit")
        play_mock.assert_called_once()
        path_arg, volume_arg = play_mock.call_args[0]
        assert path_arg.suffix == ".mp3"
        assert volume_arg == 50


class TestCmdToggle:
    def test_absent_config_toggles_to_disabled(self, tmp_config, capsys):
        npc.cmd_toggle()
        assert capsys.readouterr().out.strip() == "disabled"
        assert json.loads(tmp_config.read_text())["enabled"] is False

    def test_enabled_false_toggles_to_enabled(self, tmp_config, capsys):
        tmp_config.write_text('{"enabled": false}')
        npc.cmd_toggle()
        assert capsys.readouterr().out.strip() == "enabled"
        assert json.loads(tmp_config.read_text())["enabled"] is True

    def test_enabled_true_toggles_to_disabled(self, tmp_config, capsys):
        tmp_config.write_text('{"enabled": true}')
        npc.cmd_toggle()
        assert capsys.readouterr().out.strip() == "disabled"
        assert json.loads(tmp_config.read_text())["enabled"] is False

    def test_preserves_other_keys(self, tmp_config, capsys):
        tmp_config.write_text('{"enabled": true, "volume": 75, "language": "ru"}')
        npc.cmd_toggle()
        saved = json.loads(tmp_config.read_text())
        assert saved["volume"] == 75
        assert saved["language"] == "ru"
        assert saved["enabled"] is False

    def test_double_toggle_returns_to_original(self, tmp_config, capsys):
        tmp_config.write_text('{"enabled": true}')
        npc.cmd_toggle()
        npc.cmd_toggle()
        assert json.loads(tmp_config.read_text())["enabled"] is True


class TestCmdVolume:
    def test_sets_volume_and_prints_done(self, tmp_config, capsys):
        npc.cmd_volume(80)
        assert capsys.readouterr().out.strip() == "done"
        assert json.loads(tmp_config.read_text())["volume"] == 80

    def test_boundary_zero(self, tmp_config, capsys):
        npc.cmd_volume(0)
        assert json.loads(tmp_config.read_text())["volume"] == 0

    def test_boundary_100(self, tmp_config, capsys):
        npc.cmd_volume(100)
        assert json.loads(tmp_config.read_text())["volume"] == 100

    def test_preserves_other_keys(self, tmp_config, capsys):
        tmp_config.write_text('{"enabled": false, "volume": 20}')
        npc.cmd_volume(60)
        saved = json.loads(tmp_config.read_text())
        assert saved["enabled"] is False
        assert saved["volume"] == 60


class TestCmdLang:
    def test_sets_two_letter_code(self, tmp_config, capsys):
        npc.cmd_lang("ru")
        assert capsys.readouterr().out.strip() == "done"
        assert json.loads(tmp_config.read_text())["language"] == "ru"

    def test_auto_removes_language_key(self, tmp_config, capsys):
        tmp_config.write_text('{"language": "ru"}')
        npc.cmd_lang("auto")
        capsys.readouterr()
        assert "language" not in json.loads(tmp_config.read_text())

    def test_auto_on_config_without_language_key(self, tmp_config, capsys):
        tmp_config.write_text('{"enabled": true}')
        npc.cmd_lang("auto")
        saved = json.loads(tmp_config.read_text())
        assert "language" not in saved
        assert saved["enabled"] is True

    def test_overwrites_existing_language(self, tmp_config, capsys):
        tmp_config.write_text('{"language": "en"}')
        npc.cmd_lang("fr")
        assert json.loads(tmp_config.read_text())["language"] == "fr"


class TestCmdStatus:
    def test_empty_config_returns_defaults(self, tmp_config, monkeypatch, capsys):
        monkeypatch.setattr(npc, "_detect_system_lang", lambda: "")
        npc.cmd_status()
        out = json.loads(capsys.readouterr().out)
        assert out == {
            "enabled": True,
            "theme": "warcraft3",
            "volume": 20,
            "language": None,
            "detected_lang": None,
        }

    def test_reflects_saved_config(self, tmp_config, monkeypatch, capsys):
        tmp_config.write_text('{"enabled": false, "volume": 75, "language": "ru"}')
        monkeypatch.setattr(npc, "_detect_system_lang", lambda: "")
        npc.cmd_status()
        out = json.loads(capsys.readouterr().out)
        assert out["enabled"] is False
        assert out["volume"] == 75
        assert out["language"] == "ru"
        assert out["detected_lang"] is None

    def test_auto_lang_with_detected(self, tmp_config, monkeypatch, capsys):
        monkeypatch.setattr(npc, "_detect_system_lang", lambda: "fr")
        npc.cmd_status()
        out = json.loads(capsys.readouterr().out)
        assert out["language"] is None
        assert out["detected_lang"] == "fr"

    def test_auto_lang_detection_empty_gives_none(self, tmp_config, monkeypatch, capsys):
        monkeypatch.setattr(npc, "_detect_system_lang", lambda: "")
        npc.cmd_status()
        out = json.loads(capsys.readouterr().out)
        assert out["detected_lang"] is None

    def test_explicit_lang_skips_detection(self, tmp_config, monkeypatch, capsys):
        tmp_config.write_text('{"language": "ru"}')
        detect_calls = []
        monkeypatch.setattr(npc, "_detect_system_lang", lambda: detect_calls.append(1) or "xx")
        npc.cmd_status()
        out = json.loads(capsys.readouterr().out)
        assert out["language"] == "ru"
        assert out["detected_lang"] is None
        assert detect_calls == []

    def test_output_is_valid_json(self, tmp_config, monkeypatch, capsys):
        monkeypatch.setattr(npc, "_detect_system_lang", lambda: "")
        npc.cmd_status()
        raw = capsys.readouterr().out.strip()
        parsed = json.loads(raw)
        assert isinstance(parsed, dict)
