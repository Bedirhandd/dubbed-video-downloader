from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from dubbed_video_downloader.cli import app
from tests.conftest import expected_config_yaml


def test_config_init_default_allows_partial_override(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    with patch("dubbed_video_downloader.cli.shutil.which", return_value=None):
        result = cli_runner.invoke(
            app,
            ["config", "init", "--default", "--default-lang", "tr"],
            env={"HOME": str(tmpdir)},
        )
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    assert result.exit_code == 0, result.output
    assert config_path.read_text(encoding="utf-8") == expected_config_yaml(
        default_lang="tr"
    )


def test_config_init_default_writes_config_without_prompts(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    with (
        patch("dubbed_video_downloader.cli._stdin_is_interactive", return_value=True),
        patch("dubbed_video_downloader.cli.shutil.which", return_value=None),
    ):
        result = cli_runner.invoke(
            app, ["config", "init", "--default"], env={"HOME": str(tmpdir)}
        )
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    assert result.exit_code == 0, result.output
    assert config_path.read_text(encoding="utf-8") == expected_config_yaml()
    assert "(press Enter to use)" not in result.output


def test_config_init_writes_custom_ask_for_disk_usage(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    result = cli_runner.invoke(
        app, ["config", "init", "--ask-for-disk-usage"], env={"HOME": str(tmpdir)}
    )
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    assert result.exit_code == 0, result.output
    assert "ask_for_disk_usage: true\n" in config_path.read_text(encoding="utf-8")


def test_config_init_writes_custom_default_download_mode(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    result = cli_runner.invoke(
        app,
        ["config", "init", "--default-download-mode", "audio"],
        env={"HOME": str(tmpdir)},
    )
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    assert result.exit_code == 0, result.output
    assert "default_download_mode: audio\n" in config_path.read_text(encoding="utf-8")


def test_config_init_writes_custom_default_exists_behavior(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    result = cli_runner.invoke(
        app,
        ["config", "init", "--default-exists-behavior", "fail"],
        env={"HOME": str(tmpdir)},
    )
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    assert result.exit_code == 0, result.output
    assert "default_exists_behavior: fail\n" in config_path.read_text(encoding="utf-8")


def test_config_init_writes_custom_default_lang(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    result = cli_runner.invoke(
        app, ["config", "init", "--default-lang", "tr"], env={"HOME": str(tmpdir)}
    )
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    assert result.exit_code == 0, result.output
    assert "default_lang: tr\n" in config_path.read_text(encoding="utf-8")


def test_config_init_writes_default_config(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    result = cli_runner.invoke(app, ["config", "init"], env={"HOME": str(tmpdir)})
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    assert result.exit_code == 0, result.output
    assert (
        config_path.read_text(encoding="utf-8")
        == "output_dir: ~/Downloads/dbdvdl-output\nffmpeg_path: ffmpeg\ndefault_lang: en\ndefault_download_mode: video\ndefault_video_quality: best\ndefault_audio_quality: best\nretry_on_network_failure: 3\ndefault_exists_behavior: skip\nask_for_disk_usage: false\n"
    )


def test_init_default_allows_partial_override(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    with patch("dubbed_video_downloader.cli.shutil.which", return_value=None):
        result = cli_runner.invoke(
            app,
            ["init", "--default", "--default-lang", "tr"],
            env={"HOME": str(tmpdir)},
        )
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    assert result.exit_code == 0, result.output
    assert config_path.read_text(encoding="utf-8") == expected_config_yaml(
        default_lang="tr"
    )


def test_init_default_autodetects_ffmpeg(tmp_path: Path, cli_runner: CliRunner) -> None:
    tmpdir = tmp_path
    with patch(
        "dubbed_video_downloader.cli.shutil.which", return_value="/usr/bin/ffmpeg"
    ):
        result = cli_runner.invoke(
            app, ["init", "--default"], env={"HOME": str(tmpdir)}
        )
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    assert result.exit_code == 0, result.output
    assert config_path.read_text(encoding="utf-8") == expected_config_yaml(
        ffmpeg_path="/usr/bin/ffmpeg"
    )


def test_init_default_explicit_ffmpeg_path_skips_autodetect(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    with (
        patch("dubbed_video_downloader.cli._stdin_is_interactive", return_value=True),
        patch(
            "dubbed_video_downloader.cli.shutil.which", return_value="/usr/bin/ffmpeg"
        ),
    ):
        result = cli_runner.invoke(
            app,
            ["init", "--default", "--ffmpeg-path", "/opt/ffmpeg/bin/ffmpeg"],
            env={"HOME": str(tmpdir)},
        )
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    assert result.exit_code == 0, result.output
    assert config_path.read_text(encoding="utf-8") == expected_config_yaml(
        ffmpeg_path="/opt/ffmpeg/bin/ffmpeg"
    )
    assert "(press Enter to use)" not in result.output


def test_init_default_explicit_output_dir(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    with patch("dubbed_video_downloader.cli.shutil.which", return_value=None):
        result = cli_runner.invoke(
            app,
            ["init", "--default", "--output-dir", "~/Videos/custom"],
            env={"HOME": str(tmpdir)},
        )
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    assert result.exit_code == 0, result.output
    assert config_path.read_text(encoding="utf-8") == expected_config_yaml(
        output_dir="~/Videos/custom"
    )


def test_init_default_ffmpeg_fallback_when_not_found(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    with patch("dubbed_video_downloader.cli.shutil.which", return_value=None):
        result = cli_runner.invoke(
            app, ["init", "--default"], env={"HOME": str(tmpdir)}
        )
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    assert result.exit_code == 0, result.output
    assert config_path.read_text(encoding="utf-8") == expected_config_yaml()


def test_init_default_multiple_explicit_overrides(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    with (
        patch("dubbed_video_downloader.cli._stdin_is_interactive", return_value=True),
        patch("dubbed_video_downloader.cli.shutil.which", return_value=None),
    ):
        result = cli_runner.invoke(
            app,
            [
                "init",
                "--default",
                "--default-lang",
                "tr",
                "--default-download-mode",
                "audio",
                "--default-video-quality",
                "720p",
                "--default-audio-quality",
                "low",
                "--retry-on-network-failure",
                "0",
                "--default-exists-behavior",
                "fail",
                "--no-ask-for-disk-usage",
            ],
            env={"HOME": str(tmpdir)},
        )
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    assert result.exit_code == 0, result.output
    assert config_path.read_text(encoding="utf-8") == expected_config_yaml(
        default_lang="tr",
        default_download_mode="audio",
        default_video_quality="720p",
        default_audio_quality="low",
        retry_on_network_failure="0",
        default_exists_behavior="fail",
        ask_for_disk_usage="false",
    )
    assert "(press Enter to use)" not in result.output


def test_init_default_still_requires_force_to_overwrite(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    first = cli_runner.invoke(app, ["init", "--default"], env={"HOME": str(tmpdir)})
    with patch("dubbed_video_downloader.cli._stdin_is_interactive", return_value=True):
        second = cli_runner.invoke(
            app, ["init", "--default"], env={"HOME": str(tmpdir)}
        )
    assert first.exit_code == 0, first.output
    assert second.exit_code == 1, second.output
    assert "--force" in second.output
    assert "Output directory" not in second.output
    assert "(press Enter to use)" not in second.output


def test_init_default_with_force_overwrites_existing_config(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    first = cli_runner.invoke(app, ["init", "--default"], env={"HOME": str(tmpdir)})
    with (
        patch("dubbed_video_downloader.cli._stdin_is_interactive", return_value=True),
        patch("dubbed_video_downloader.cli.shutil.which", return_value=None),
    ):
        second = cli_runner.invoke(
            app,
            ["init", "--default", "--force", "--default-lang", "tr"],
            env={"HOME": str(tmpdir)},
        )
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    assert first.exit_code == 0, first.output
    assert second.exit_code == 0, second.output
    assert config_path.read_text(encoding="utf-8") == expected_config_yaml(
        default_lang="tr"
    )
    assert "(press Enter to use)" not in second.output


def test_init_default_writes_config_without_prompts(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    with (
        patch("dubbed_video_downloader.cli._stdin_is_interactive", return_value=True),
        patch("dubbed_video_downloader.cli.shutil.which", return_value=None),
    ):
        result = cli_runner.invoke(
            app, ["init", "--default"], env={"HOME": str(tmpdir)}
        )
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    assert result.exit_code == 0, result.output
    assert config_path.read_text(encoding="utf-8") == expected_config_yaml()
    assert "(press Enter to use)" not in result.output
    assert "Downloads will be saved under this directory." not in result.output


def test_init_refuses_overwrite_without_force(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    first = cli_runner.invoke(app, ["init"], env={"HOME": str(tmpdir)})
    second = cli_runner.invoke(app, ["init"], env={"HOME": str(tmpdir)})
    assert first.exit_code == 0, first.output
    assert second.exit_code == 1, second.output
    assert "--force" in second.output
    assert "Output directory" not in second.output
    assert "(press Enter to use)" not in second.output


def test_init_writes_custom_ask_for_disk_usage(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    result = cli_runner.invoke(
        app, ["init", "--ask-for-disk-usage"], env={"HOME": str(tmpdir)}
    )
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    assert result.exit_code == 0, result.output
    assert "ask_for_disk_usage: true\n" in config_path.read_text(encoding="utf-8")


def test_init_writes_custom_default_download_mode(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    result = cli_runner.invoke(
        app, ["init", "--default-download-mode", "audio"], env={"HOME": str(tmpdir)}
    )
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    assert result.exit_code == 0, result.output
    assert "default_download_mode: audio\n" in config_path.read_text(encoding="utf-8")


def test_init_writes_custom_default_exists_behavior(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    result = cli_runner.invoke(
        app,
        ["init", "--default-exists-behavior", "overwrite"],
        env={"HOME": str(tmpdir)},
    )
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    assert result.exit_code == 0, result.output
    assert "default_exists_behavior: overwrite\n" in config_path.read_text(
        encoding="utf-8"
    )


def test_init_writes_custom_default_lang(tmp_path: Path, cli_runner: CliRunner) -> None:
    tmpdir = tmp_path
    result = cli_runner.invoke(
        app, ["init", "--default-lang", "tr"], env={"HOME": str(tmpdir)}
    )
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    assert result.exit_code == 0, result.output
    assert "default_lang: tr\n" in config_path.read_text(encoding="utf-8")


def test_init_writes_custom_default_qualities(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    result = cli_runner.invoke(
        app,
        ["init", "--default-video-quality", "720p", "--default-audio-quality", "low"],
        env={"HOME": str(tmpdir)},
    )
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    assert result.exit_code == 0, result.output
    written_config = config_path.read_text(encoding="utf-8")
    assert "default_video_quality: 720p\n" in written_config
    assert "default_audio_quality: low\n" in written_config


def test_init_writes_custom_retry_on_network_failure(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    result = cli_runner.invoke(
        app, ["init", "--retry-on-network-failure", "5"], env={"HOME": str(tmpdir)}
    )
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    assert result.exit_code == 0, result.output
    assert "retry_on_network_failure: 5\n" in config_path.read_text(encoding="utf-8")


def test_init_writes_default_config(tmp_path: Path, cli_runner: CliRunner) -> None:
    tmpdir = tmp_path
    result = cli_runner.invoke(app, ["init"], env={"HOME": str(tmpdir)})
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    assert result.exit_code == 0, result.output
    assert config_path.read_text(encoding="utf-8") == expected_config_yaml()


def test_init_writes_normalized_default_lang(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    result = cli_runner.invoke(
        app, ["init", "--default-lang", "eng"], env={"HOME": str(tmpdir)}
    )
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    assert result.exit_code == 0, result.output
    assert "default_lang: en\n" in config_path.read_text(encoding="utf-8")


def test_interactive_config_init_explains_prompts_and_keeps_defaults(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    with patch("dubbed_video_downloader.cli._stdin_is_interactive", return_value=True):
        result = cli_runner.invoke(
            app,
            ["config", "init"],
            input="\n\n\n\n\n\n\n\n\n",
            env={"HOME": str(tmpdir)},
        )
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    assert result.exit_code == 0, result.output
    assert "Accepted: `video` | `audio`." in result.output
    assert "(`144p`-`8640p`, e.g. `720p`)" in result.output
    assert result.output.count("(press Enter to use)") == 9
    assert "Hint:" not in result.output
    assert (
        config_path.read_text(encoding="utf-8")
        == "output_dir: ~/Downloads/dbdvdl-output\nffmpeg_path: ffmpeg\ndefault_lang: en\ndefault_download_mode: video\ndefault_video_quality: best\ndefault_audio_quality: best\nretry_on_network_failure: 3\ndefault_exists_behavior: skip\nask_for_disk_usage: false\n"
    )


def test_interactive_init_colors_prompt_keys(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    with patch("dubbed_video_downloader.cli._stdin_is_interactive", return_value=True):
        result = cli_runner.invoke(
            app,
            ["init"],
            input="\n\n\n\n\n\n\n\n\n",
            env={"HOME": str(tmpdir)},
            color=True,
        )
    assert result.exit_code == 0, result.output
    assert "\x1b[36m\x1b[1mOutput directory" in result.output
    assert "\x1b[36m\x1b[1mAccepted:" in result.output
    assert "\x1b[36m\x1b[1mDefault:" in result.output
    assert "\x1b[36m\x1b[1mHint:" not in result.output


def test_interactive_init_explains_each_prompt(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    with patch("dubbed_video_downloader.cli._stdin_is_interactive", return_value=True):
        result = cli_runner.invoke(
            app, ["init"], input="\n\n\n\n\n\n\n\n\n", env={"HOME": str(tmpdir)}
        )
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    assert result.exit_code == 0, result.output
    assert "Downloads will be saved under this directory." in result.output
    assert "Accepted: absolute path, ~ path, or env-var path." in result.output
    assert "Executable used to merge video and dubbed audio." in result.output
    assert "Accepted: `ffmpeg`, `ffmpeg.exe`, or absolute path." in result.output
    assert "Dub language code to use when --lang is omitted." in result.output
    assert "Accepted: BCP-47 language code, e.g. en, eng, en-US, tr." in result.output
    assert "Which type of output to download" in result.output
    assert "Accepted: `video` | `audio`." in result.output
    assert "Which video quality to select" in result.output
    assert "(`144p`-`8640p`, e.g. `720p`)" in result.output
    assert "Which dubbed audio quality to select" in result.output
    assert "Accepted: `best` | `medium` | `low`." in result.output
    assert "How many times to retry transient metadata" in result.output
    assert "Accepted: non-negative integer; 0 disables retries." in result.output
    assert "What to do when the planned output file already exists." in result.output
    assert "Accepted: `skip` | `fail` | `overwrite`." in result.output
    assert (
        "Whether downloads should ask for confirmation after estimating size."
        in result.output
    )
    assert "Accepted: `yes` | `no`." in result.output
    assert result.output.count("(press Enter to use)") == 9
    assert "Hint:" not in result.output
    assert "Default: ~/Downloads/dbdvdl-output (press Enter to use)" in result.output
    assert "Default: ffmpeg (press Enter to use)" in result.output
    assert "Default: en (press Enter to use)" in result.output
    assert "Default: video (press Enter to use)" in result.output
    assert "Default: best (press Enter to use)" in result.output
    assert "Default: 3 (press Enter to use)" in result.output
    assert "Default: skip (press Enter to use)" in result.output
    assert "Default: false (press Enter to use)" in result.output
    assert (
        config_path.read_text(encoding="utf-8")
        == "output_dir: ~/Downloads/dbdvdl-output\nffmpeg_path: ffmpeg\ndefault_lang: en\ndefault_download_mode: video\ndefault_video_quality: best\ndefault_audio_quality: best\nretry_on_network_failure: 3\ndefault_exists_behavior: skip\nask_for_disk_usage: false\n"
    )


def test_interactive_init_explicit_lang_skips_language_prompt(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    with patch("dubbed_video_downloader.cli._stdin_is_interactive", return_value=True):
        result = cli_runner.invoke(
            app,
            ["init", "--default-lang", "tr"],
            input="\n\n\n\n\n\n\n\n",
            env={"HOME": str(tmpdir)},
        )
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    assert result.exit_code == 0, result.output
    assert "default_lang: tr\n" in config_path.read_text(encoding="utf-8")
    assert "Dub language code to use when --lang is omitted." not in result.output
    assert result.output.count("(press Enter to use)") == 8


def test_interactive_init_refuses_overwrite_before_prompts(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    first = cli_runner.invoke(app, ["init"], env={"HOME": str(tmpdir)})
    with patch("dubbed_video_downloader.cli._stdin_is_interactive", return_value=True):
        second = cli_runner.invoke(
            app, ["init"], input="\n\n\n\n\n\n\n\n\n", env={"HOME": str(tmpdir)}
        )
    assert first.exit_code == 0, first.output
    assert second.exit_code == 1, second.output
    assert "--force" in second.output
    assert "Output directory" not in second.output
    assert "(press Enter to use)" not in second.output
