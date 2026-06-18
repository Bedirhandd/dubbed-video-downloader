from __future__ import annotations

from pathlib import Path

import pytest
from tests.support import live_helpers
from typer.testing import CliRunner

from dubbed_video_downloader import core, errors, languages
from dubbed_video_downloader.cli import app

pytestmark = pytest.mark.live


def test_live_download_audio(
    live_test_url: str,
    live_test_lang: str,
    live_output_dir: Path,
) -> None:
    result = core.download(
        url=live_test_url,
        lang=live_test_lang,
        download_mode=core.DownloadMode.AUDIO,
        output_dir=live_output_dir,
        audio_quality="low",
        exists_behavior=core.FileExistsBehavior.OVERWRITE,
    )
    assert result.status == core.DownloadStatus.DOWNLOADED
    assert result.output_path is not None
    live_helpers.assert_output_under_language_dir(
        result.output_path,
        live_test_lang,
        live_output_dir,
    )


def test_live_download_video(
    live_test_url: str,
    live_test_lang: str,
    live_output_dir: Path,
) -> None:
    result = core.download(
        url=live_test_url,
        lang=live_test_lang,
        download_mode=core.DownloadMode.VIDEO,
        output_dir=live_output_dir,
        video_quality="low",
        audio_quality="low",
        exists_behavior=core.FileExistsBehavior.OVERWRITE,
    )
    assert result.status == core.DownloadStatus.DOWNLOADED
    assert result.output_path is not None
    assert result.output_path.suffix == ".mkv"
    live_helpers.assert_output_under_language_dir(
        result.output_path,
        live_test_lang,
        live_output_dir,
    )


def test_live_plan_download_detects_existing_output(
    live_test_url: str,
    live_test_lang: str,
    live_output_dir: Path,
) -> None:
    plan = core.plan_download(
        url=live_test_url,
        lang=live_test_lang,
        output_dir=live_output_dir,
        video_quality="low",
        audio_quality="low",
    )
    assert plan.output_exists is True
    assert plan.output_path.is_file()


def test_live_cli_download_audio(
    live_test_url: str,
    live_test_lang: str,
    live_cli_env: dict[str, str],
    cli_runner: CliRunner,
) -> None:
    result = cli_runner.invoke(
        app,
        [
            "download",
            live_test_url,
            "--lang",
            live_test_lang,
            "--mode",
            "audio",
            "--audio-quality",
            "low",
            "--if-exists",
            "overwrite",
            "--yes",
        ],
        env=live_cli_env,
    )
    assert result.exit_code == 0, result.output
    assert "Saved to" in result.output or "saved" in result.output.lower()


def test_live_plan_download_invalid_language(
    live_test_url: str,
    live_language_inventory: languages.AudioLanguageInventory,
    live_output_dir: Path,
) -> None:
    missing_lang = live_helpers.unavailable_language(live_language_inventory)
    with pytest.raises(errors.LanguageNotFoundError):
        core.plan_download(
            url=live_test_url,
            lang=missing_lang,
            output_dir=live_output_dir,
        )


def test_live_cli_download_invalid_language(
    live_test_url: str,
    live_language_inventory: languages.AudioLanguageInventory,
    live_cli_env: dict[str, str],
    cli_runner: CliRunner,
) -> None:
    missing_lang = live_helpers.unavailable_language(live_language_inventory)
    result = cli_runner.invoke(
        app,
        [
            "download",
            live_test_url,
            "--lang",
            missing_lang,
            "--dry-run",
        ],
        env=live_cli_env,
    )
    assert result.exit_code == 1, result.output


def test_live_no_stale_incomplete_after_downloads(live_output_dir: Path) -> None:
    live_helpers.assert_no_stale_incomplete_runs(live_output_dir)
