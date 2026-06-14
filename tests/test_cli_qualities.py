from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from dubbed_video_downloader import core, errors
from dubbed_video_downloader.cli import app


def test_qualities_rejects_invalid_lang_before_network_work(
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
    with patch("dubbed_video_downloader.cli.core.get_quality_report") as report:
        result = cli_runner.invoke(
            app,
            ["qualities", "https://www.youtube.com/watch?v=EXAMPLE", "--lang", "jp"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 1, result.output
    assert "Input error:" in result.output
    assert "--lang" in result.output
    assert "default_lang" not in result.output
    assert "Config error:" not in result.output
    report.assert_not_called()


def test_qualities_reports_domain_error_traceback_with_debug(
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
        "dubbed_video_downloader.cli.core.get_quality_report",
        side_effect=errors.LanguageNotFoundError("missing language"),
    ) as report:
        result = cli_runner.invoke(
            app,
            ["qualities", "https://www.youtube.com/watch?v=EXAMPLE", "--debug"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 1, result.output
    report.assert_called_once()
    assert "Error: missing language" in result.output
    assert "Traceback" in result.output


def test_qualities_reports_domain_error_without_traceback(
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
        "dubbed_video_downloader.cli.core.get_quality_report",
        side_effect=errors.LanguageNotFoundError("missing language"),
    ) as report:
        result = cli_runner.invoke(
            app,
            ["qualities", "https://www.youtube.com/watch?v=EXAMPLE"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 1, result.output
    report.assert_called_once()
    assert "Error: missing language" in result.output
    assert "Traceback" not in result.output


def test_qualities_requires_config_before_network_work(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    with patch("dubbed_video_downloader.cli.core.get_quality_report") as report:
        result = cli_runner.invoke(
            app,
            ["qualities", "https://www.youtube.com/watch?v=EXAMPLE"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 1, result.output
    assert "dbdvdl init" in result.output
    report.assert_not_called()


def test_qualities_uses_config_and_allows_lang_override(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\nretry_on_network_failure: 4\n",
        encoding="utf-8",
    )
    with patch(
        "dubbed_video_downloader.cli.core.get_quality_report",
        return_value=core.QualityReport(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            resolved_lang="tr",
            title="Title",
            uploader="Channel",
            available_langs=("en", "tr"),
            video_qualities=("360p", "720p"),
            audio_qualities=("50k", "160k"),
        ),
    ) as report:
        result = cli_runner.invoke(
            app,
            [
                "qualities",
                "https://www.youtube.com/watch?v=EXAMPLE",
                "--lang",
                "tr",
                "--retry-on-network-failure",
                "6",
            ],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 0, result.output
    report.assert_called_once_with(
        "https://www.youtube.com/watch?v=EXAMPLE",
        "tr",
        verbose=False,
        debug=False,
        retry_on_network_failure=6,
    )
    assert "Video qualities: 360p, 720p" in result.output
    assert "Audio qualities: 50k, 160k" in result.output
