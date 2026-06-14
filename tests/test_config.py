from __future__ import annotations

from pathlib import Path

import pytest

from dubbed_video_downloader import config


def test_missing_config_fails_with_init_hint(tmp_path: Path) -> None:
    missing_path = tmp_path / "config.yaml"

    with pytest.raises(config.ConfigError, match="Run `dbdvdl init`"):
        config.load_config(missing_path)


def test_valid_config_loads_and_expands_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path
    config_path = home / "config.yaml"
    config_path.write_text(
        "output_dir: ~/Videos\n"
        "ffmpeg_path: $HOME/bin/ffmpeg\n"
        "default_lang: en\n"
        "default_download_mode: audio\n"
        "default_video_quality: 720p\n"
        "default_audio_quality: low\n"
        "retry_on_network_failure: 5\n"
        "default_exists_behavior: overwrite\n"
        "ask_for_disk_usage: true\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("HOME", str(home))
    loaded_config = config.load_config(config_path)

    assert loaded_config.output_dir == home / "Videos"
    assert loaded_config.ffmpeg_path == str(home / "bin" / "ffmpeg")
    assert loaded_config.default_lang == "en"
    assert loaded_config.default_download_mode == config.DownloadMode.AUDIO
    assert loaded_config.default_video_quality.label == "720p"
    assert loaded_config.default_audio_quality.label == "low"
    assert loaded_config.retry_on_network_failure == 5
    assert loaded_config.default_exists_behavior == config.FileExistsBehavior.OVERWRITE
    assert loaded_config.ask_for_disk_usage


def test_missing_optional_keys_use_defaults() -> None:
    loaded_config = config.config_from_mapping(
        {
            "output_dir": "/tmp/dbdvdl-output",
            "ffmpeg_path": "ffmpeg",
            "default_lang": "en",
        }
    )

    assert loaded_config.output_dir == Path("/tmp/dbdvdl-output")
    assert loaded_config.ffmpeg_path == "ffmpeg"
    assert loaded_config.default_lang == "en"
    assert loaded_config.default_download_mode == config.DEFAULT_DOWNLOAD_MODE
    assert loaded_config.default_video_quality == config.DEFAULT_VIDEO_QUALITY
    assert loaded_config.default_audio_quality == config.DEFAULT_AUDIO_QUALITY
    assert (
        loaded_config.retry_on_network_failure
        == config.DEFAULT_RETRY_ON_NETWORK_FAILURE
    )
    assert loaded_config.default_exists_behavior == config.DEFAULT_EXISTS_BEHAVIOR
    assert loaded_config.ask_for_disk_usage == config.DEFAULT_ASK_FOR_DISK_USAGE


def test_unknown_keys_are_ignored() -> None:
    loaded_config = config.config_from_mapping(
        {
            "output_dir": "/tmp/dbdvdl-output",
            "ffmpeg_path": "ffmpeg",
            "default_lang": "en",
            "default_download_mode": "audio",
            "default_video_quality": "1080p",
            "default_audio_quality": "medium",
            "retry_on_network_failure": 4,
            "default_exists_behavior": "fail",
            "ask_for_disk_usage": True,
            "future": "accepted",
        }
    )

    assert loaded_config.output_dir == Path("/tmp/dbdvdl-output")
    assert loaded_config.ffmpeg_path == "ffmpeg"
    assert loaded_config.default_lang == "en"
    assert loaded_config.default_download_mode == config.DownloadMode.AUDIO
    assert loaded_config.default_video_quality.label == "1080p"
    assert loaded_config.default_audio_quality.label == "medium"
    assert loaded_config.retry_on_network_failure == 4
    assert loaded_config.default_exists_behavior == config.FileExistsBehavior.FAIL
    assert loaded_config.ask_for_disk_usage


def test_missing_ffmpeg_path_fails() -> None:
    with pytest.raises(config.ConfigError, match="ffmpeg_path"):
        config.config_from_mapping(
            {
                "output_dir": "/tmp/dbdvdl-output",
                "default_lang": "en",
            }
        )


def test_missing_default_lang_fails() -> None:
    with pytest.raises(config.ConfigError, match="default_lang"):
        config.config_from_mapping(
            {
                "output_dir": "/tmp/dbdvdl-output",
                "ffmpeg_path": "ffmpeg",
            }
        )


def test_wrong_ffmpeg_path_type_fails() -> None:
    with pytest.raises(config.ConfigError, match="ffmpeg_path"):
        config.config_from_mapping(
            {
                "output_dir": "/tmp/dbdvdl-output",
                "ffmpeg_path": 123,
                "default_lang": "en",
            }
        )


def test_wrong_default_lang_type_fails() -> None:
    with pytest.raises(config.ConfigError, match="default_lang"):
        config.config_from_mapping(
            {
                "output_dir": "/tmp/dbdvdl-output",
                "ffmpeg_path": "ffmpeg",
                "default_lang": 123,
            }
        )


def test_empty_default_lang_fails() -> None:
    with pytest.raises(config.ConfigError, match="default_lang"):
        config.normalize_default_lang(" ")


def test_default_lang_normalizes_aliases() -> None:
    assert config.normalize_default_lang("eng") == "en"
    assert config.normalize_default_lang("en_uk") == "en-GB"


def test_invalid_default_lang_fails() -> None:
    with pytest.raises(config.ConfigError, match="default_lang"):
        config.normalize_default_lang("jp")


def test_load_config_accepts_unnormalized_default_lang() -> None:
    loaded_config = config.config_from_mapping(
        {
            "output_dir": "/tmp/dbdvdl-output",
            "ffmpeg_path": "ffmpeg",
            "default_lang": "jp",
        }
    )

    assert loaded_config.default_lang == "jp"


def test_download_mode_accepts_video_and_audio() -> None:
    assert config.normalize_download_mode("video") == config.DownloadMode.VIDEO
    assert config.normalize_download_mode("audio") == config.DownloadMode.AUDIO


def test_invalid_download_mode_fails() -> None:
    with pytest.raises(config.ConfigError, match="default_download_mode"):
        config.normalize_download_mode("mp3")


def test_wrong_download_mode_type_fails() -> None:
    with pytest.raises(config.ConfigError, match="default_download_mode"):
        config.normalize_download_mode(123)


def test_exists_behavior_accepts_supported_values() -> None:
    assert config.normalize_exists_behavior("skip") == config.FileExistsBehavior.SKIP
    assert config.normalize_exists_behavior(" fail ") == config.FileExistsBehavior.FAIL
    assert (
        config.normalize_exists_behavior("overwrite")
        == config.FileExistsBehavior.OVERWRITE
    )


def test_invalid_exists_behavior_fails() -> None:
    with pytest.raises(config.ConfigError, match="default_exists_behavior"):
        config.normalize_exists_behavior("replace")


def test_wrong_exists_behavior_type_fails() -> None:
    with pytest.raises(config.ConfigError, match="default_exists_behavior"):
        config.normalize_exists_behavior(True)


def test_video_quality_accepts_presets_and_exact_resolutions() -> None:
    assert config.normalize_video_quality("best").label == "best"
    assert config.normalize_video_quality(" medium ").label == "medium"
    assert config.normalize_video_quality("720P").label == "720p"


@pytest.mark.parametrize("value", ["1p", "0p", "-100p", "720", "720 p", "", "abc"])
def test_invalid_video_quality_fails(value: str) -> None:
    with pytest.raises(config.ConfigError, match="default_video_quality"):
        config.normalize_video_quality(value)


@pytest.mark.parametrize("value", [None, True, ["720p"], {"quality": "720p"}])
def test_wrong_video_quality_type_fails(value: object) -> None:
    with pytest.raises(config.ConfigError, match="default_video_quality"):
        config.normalize_video_quality(value)


def test_audio_quality_accepts_presets() -> None:
    assert config.normalize_audio_quality("best").label == "best"
    assert config.normalize_audio_quality(" LOW ").label == "low"


@pytest.mark.parametrize("value", ["128k", "720p", "", "abc"])
def test_invalid_audio_quality_fails(value: str) -> None:
    with pytest.raises(config.ConfigError, match="default_audio_quality"):
        config.normalize_audio_quality(value)


@pytest.mark.parametrize("value", [None, False, ["best"], {"quality": "best"}])
def test_wrong_audio_quality_type_fails(value: object) -> None:
    with pytest.raises(config.ConfigError, match="default_audio_quality"):
        config.normalize_audio_quality(value)


def test_zero_retry_on_network_failure_is_allowed() -> None:
    assert config.normalize_retry_on_network_failure(0) == 0


def test_negative_retry_on_network_failure_fails() -> None:
    with pytest.raises(config.ConfigError, match="retry_on_network_failure"):
        config.normalize_retry_on_network_failure(-1)


def test_string_retry_on_network_failure_fails() -> None:
    with pytest.raises(config.ConfigError, match="retry_on_network_failure"):
        config.normalize_retry_on_network_failure("3")


def test_bool_retry_on_network_failure_fails() -> None:
    with pytest.raises(config.ConfigError, match="retry_on_network_failure"):
        config.normalize_retry_on_network_failure(True)


def test_ask_for_disk_usage_accepts_booleans() -> None:
    assert config.normalize_ask_for_disk_usage(True)
    assert not config.normalize_ask_for_disk_usage(False)


@pytest.mark.parametrize("value", ["true", 1, None])
def test_ask_for_disk_usage_rejects_non_booleans(value: object) -> None:
    with pytest.raises(config.ConfigError, match="ask_for_disk_usage"):
        config.normalize_ask_for_disk_usage(value)


def test_relative_output_dir_fails() -> None:
    with pytest.raises(config.ConfigError, match="absolute path"):
        config.normalize_output_dir("Videos")


def test_relative_ffmpeg_path_fails() -> None:
    with pytest.raises(config.ConfigError, match="ffmpeg"):
        config.normalize_ffmpeg_path("bin/ffmpeg")
