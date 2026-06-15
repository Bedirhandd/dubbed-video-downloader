from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from dubbed_video_downloader import errors
from dubbed_video_downloader.cli import app
from tests.support.cli_helpers import audio_inventory, plain_cli_output


def test_langs_help_includes_verbose(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(app, ["langs", "--help"])
    plain_output = plain_cli_output(result.output)
    assert result.exit_code == 0, result.output
    assert "verbose" in plain_output
    assert "debug" in plain_output
    assert "retry-on-network" in plain_output


def test_langs_passes_debug_true(tmp_path: Path, cli_runner: CliRunner) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\n",
        encoding="utf-8",
    )
    with patch(
        "dubbed_video_downloader.cli.core.get_audio_language_inventory_for_url",
        return_value=audio_inventory("tr"),
    ) as langs:
        result = cli_runner.invoke(
            app,
            ["langs", "https://www.youtube.com/watch?v=EXAMPLE", "--debug"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 0, result.output
    langs.assert_called_once_with(
        "https://www.youtube.com/watch?v=EXAMPLE",
        verbose=False,
        debug=True,
        retry_on_network_failure=3,
    )


def test_langs_passes_verbose_false_by_default(
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
    with patch(
        "dubbed_video_downloader.cli.core.get_audio_language_inventory_for_url",
        return_value=audio_inventory("tr", "en"),
    ) as langs:
        result = cli_runner.invoke(
            app,
            ["langs", "https://www.youtube.com/watch?v=EXAMPLE"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 0, result.output
    langs.assert_called_once_with(
        "https://www.youtube.com/watch?v=EXAMPLE",
        verbose=False,
        debug=False,
        retry_on_network_failure=3,
    )
    assert "en" in result.output
    assert "tr" in result.output


def test_langs_passes_verbose_true(tmp_path: Path, cli_runner: CliRunner) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\nretry_on_network_failure: 4\n",
        encoding="utf-8",
    )
    with patch(
        "dubbed_video_downloader.cli.core.get_audio_language_inventory_for_url",
        return_value=audio_inventory("tr"),
    ) as langs:
        result = cli_runner.invoke(
            app,
            [
                "langs",
                "https://www.youtube.com/watch?v=EXAMPLE",
                "--verbose",
                "--retry-on-network-failure",
                "6",
            ],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 0, result.output
    langs.assert_called_once_with(
        "https://www.youtube.com/watch?v=EXAMPLE",
        verbose=True,
        debug=False,
        retry_on_network_failure=6,
    )


def test_langs_reports_metadata_error_traceback_with_debug(
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
    with patch(
        "dubbed_video_downloader.cli.core.get_audio_language_inventory_for_url",
        side_effect=errors.MetadataExtractionError("metadata failed"),
    ) as langs:
        result = cli_runner.invoke(
            app,
            ["langs", "https://www.youtube.com/watch?v=EXAMPLE", "--debug"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 1, result.output
    langs.assert_called_once()
    assert "Error: metadata failed" in result.output
    assert "Traceback" in result.output


def test_langs_reports_metadata_error_without_traceback(
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
    with patch(
        "dubbed_video_downloader.cli.core.get_audio_language_inventory_for_url",
        side_effect=errors.MetadataExtractionError("metadata failed"),
    ) as langs:
        result = cli_runner.invoke(
            app,
            ["langs", "https://www.youtube.com/watch?v=EXAMPLE"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 1, result.output
    langs.assert_called_once()
    assert "Error: metadata failed" in result.output
    assert "Traceback" not in result.output


def test_langs_reports_unexpected_metadata_shape_error(
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
    with patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl:
        ydl = youtube_dl.return_value.__enter__.return_value
        ydl.extract_info.return_value = None
        result = cli_runner.invoke(
            app,
            ["langs", "https://www.youtube.com/watch?v=EXAMPLE"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 1, result.output
    assert "Error:" in result.output
    assert "unexpected metadata shape" in result.output
    assert "Traceback" not in result.output


def test_langs_requires_config_before_network_work(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    with patch(
        "dubbed_video_downloader.cli.core.get_audio_language_inventory_for_url"
    ) as langs:
        result = cli_runner.invoke(
            app,
            ["langs", "https://www.youtube.com/watch?v=EXAMPLE"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 1, result.output
    assert "dbdvdl init" in result.output
    langs.assert_not_called()


def test_langs_works_with_invalid_default_lang_in_config(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: jp\n",
        encoding="utf-8",
    )
    with patch(
        "dubbed_video_downloader.cli.core.get_audio_language_inventory_for_url",
        return_value=audio_inventory("tr", "en"),
    ):
        result = cli_runner.invoke(
            app,
            ["langs", "https://www.youtube.com/watch?v=EXAMPLE"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 0, result.output
    assert "Config error:" not in result.output
    assert "en" in result.output
    assert "tr" in result.output
