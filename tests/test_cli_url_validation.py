from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from dubbed_video_downloader import core
from dubbed_video_downloader.cli import app
from tests.support.cli_helpers import audio_inventory

VALID_HTTPS_URL = "https://www.youtube.com/watch?v=EXAMPLE"
VALID_HTTP_URL = "http://www.youtube.com/watch?v=EXAMPLE"
FILE_URL = "file:///tmp/x.mkv"


def _write_minimal_config(home: Path) -> None:
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    ("command", "core_target"),
    [
        (
            "langs",
            "dubbed_video_downloader.cli.core.get_audio_language_inventory_for_url",
        ),
        ("qualities", "dubbed_video_downloader.cli.core.get_quality_report"),
        ("download", "dubbed_video_downloader.cli.core.download"),
    ],
)
def test_command_rejects_file_url_before_network_work(
    tmp_path: Path,
    cli_runner: CliRunner,
    command: str,
    core_target: str,
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    _write_minimal_config(home)
    with patch(core_target) as core_call:
        result = cli_runner.invoke(
            app,
            [command, FILE_URL],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 1, result.output
    assert "Input error:" in result.output
    assert "http or https" in result.output
    core_call.assert_not_called()


def test_langs_accepts_https_url(tmp_path: Path, cli_runner: CliRunner) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    _write_minimal_config(home)
    with patch(
        "dubbed_video_downloader.cli.core.get_audio_language_inventory_for_url",
        return_value=audio_inventory("tr"),
    ) as langs:
        result = cli_runner.invoke(
            app,
            ["langs", VALID_HTTPS_URL],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 0, result.output
    langs.assert_called_once()
    assert langs.call_args.args[0] == VALID_HTTPS_URL


def test_langs_accepts_http_url(tmp_path: Path, cli_runner: CliRunner) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    _write_minimal_config(home)
    with patch(
        "dubbed_video_downloader.cli.core.get_audio_language_inventory_for_url",
        return_value=audio_inventory("tr"),
    ) as langs:
        result = cli_runner.invoke(
            app,
            ["langs", VALID_HTTP_URL],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 0, result.output
    langs.assert_called_once()
    assert langs.call_args.args[0] == VALID_HTTP_URL


def test_download_rejects_relative_url_before_network_work(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    _write_minimal_config(home)
    with (
        patch("dubbed_video_downloader.cli.core.download") as download,
        patch("dubbed_video_downloader.cli.core.plan_download") as plan,
    ):
        result = cli_runner.invoke(
            app,
            ["download", "watch?v=abc"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 1, result.output
    assert "Input error:" in result.output
    download.assert_not_called()
    plan.assert_not_called()


def test_qualities_rejects_missing_host_before_network_work(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    _write_minimal_config(home)
    with patch("dubbed_video_downloader.cli.core.get_quality_report") as report:
        result = cli_runner.invoke(
            app,
            ["qualities", "https://"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 1, result.output
    assert "Input error:" in result.output
    report.assert_not_called()


def test_download_rejects_invalid_url_in_multi_url_batch_before_network_work(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    _write_minimal_config(home)
    with (
        patch("dubbed_video_downloader.cli.core.download") as download,
        patch("dubbed_video_downloader.cli.core.plan_download") as plan,
    ):
        result = cli_runner.invoke(
            app,
            ["download", VALID_HTTPS_URL, FILE_URL],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 1, result.output
    assert "Input error:" in result.output
    download.assert_not_called()
    plan.assert_not_called()


def test_qualities_accepts_https_url(tmp_path: Path, cli_runner: CliRunner) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    _write_minimal_config(home)
    with patch(
        "dubbed_video_downloader.cli.core.get_quality_report",
        return_value=core.QualityReport(
            url=VALID_HTTPS_URL,
            lang="en",
            resolved_lang="en",
            title="Title",
            uploader="Channel",
            available_langs=("en",),
            video_qualities=("720p",),
            audio_qualities=("160k",),
        ),
    ) as report:
        result = cli_runner.invoke(
            app,
            ["qualities", VALID_HTTPS_URL],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 0, result.output
    report.assert_called_once()
    assert report.call_args.args[0] == VALID_HTTPS_URL
