from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from dubbed_video_downloader.cli import app


def test_config_remove_cancels_when_user_answers_no(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_dir = home / ".config" / "dubbed-video-downloader"
    config_dir.mkdir(parents=True)
    (config_dir / "config.yaml").write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\n",
        encoding="utf-8",
    )
    with patch("dubbed_video_downloader.cli._stdin_is_interactive", return_value=True):
        result = cli_runner.invoke(
            app, ["config", "remove"], input="n\n", env={"HOME": str(tmpdir)}
        )
    assert result.exit_code == 0, result.output
    assert config_dir.exists()
    assert "Config removal cancelled." in result.output


def test_config_remove_refuses_non_interactive_without_yes(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_dir = home / ".config" / "dubbed-video-downloader"
    config_dir.mkdir(parents=True)
    (config_dir / "config.yaml").write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\n",
        encoding="utf-8",
    )
    with patch("dubbed_video_downloader.cli._stdin_is_interactive", return_value=False):
        result = cli_runner.invoke(app, ["config", "remove"], env={"HOME": str(tmpdir)})
    assert result.exit_code == 1, result.output
    assert config_dir.exists()
    assert "--yes" in result.output


def test_config_remove_short_yes_removes_config_directory_non_interactively(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_dir = home / ".config" / "dubbed-video-downloader"
    config_dir.mkdir(parents=True)
    (config_dir / "config.yaml").write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\n",
        encoding="utf-8",
    )
    with patch("dubbed_video_downloader.cli._stdin_is_interactive", return_value=False):
        result = cli_runner.invoke(
            app, ["config", "remove", "-y"], env={"HOME": str(tmpdir)}
        )
    assert result.exit_code == 0, result.output
    assert not config_dir.exists()
    assert f"Removed config directory: {config_dir}" in result.output


def test_config_remove_yes_removes_config_directory(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_dir = home / ".config" / "dubbed-video-downloader"
    config_dir.mkdir(parents=True)
    (config_dir / "config.yaml").write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\n",
        encoding="utf-8",
    )
    result = cli_runner.invoke(
        app, ["config", "remove", "--yes"], env={"HOME": str(tmpdir)}
    )
    assert result.exit_code == 0, result.output
    assert not config_dir.exists()
    assert f"Removed config directory: {config_dir}" in result.output
    assert "dbdvdl init" in result.output


def test_config_remove_yes_succeeds_when_missing(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    result = cli_runner.invoke(
        app, ["config", "remove", "--yes"], env={"HOME": str(tmpdir)}
    )
    assert result.exit_code == 0, result.output
    assert "Nothing to remove." in result.output


def test_config_show_displays_resolved_values(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\n",
        encoding="utf-8",
    )
    result = cli_runner.invoke(app, ["config", "show"], env={"HOME": str(tmpdir)})
    assert result.exit_code == 0, result.output
    assert f"Config path: {config_path}" in result.output
    assert f"Output directory: {home / 'Downloads' / 'from-config'}" in result.output
    assert "FFmpeg path: ffmpeg" in result.output
    assert "Default language: en" in result.output
    assert "Default download mode: video" in result.output
    assert "Default video quality: best" in result.output
    assert "Default audio quality: best" in result.output
    assert "Retry on network failure: 3" in result.output
    assert "Default exists behavior: skip" in result.output
    assert "Ask for disk usage: false" in result.output


def test_config_show_requires_existing_config(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    result = cli_runner.invoke(app, ["config", "show"], env={"HOME": str(tmpdir)})
    assert result.exit_code == 1, result.output
    assert "dbdvdl init" in result.output
