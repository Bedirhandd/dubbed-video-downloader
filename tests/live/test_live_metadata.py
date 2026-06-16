from __future__ import annotations

from pathlib import Path

import pytest
from tests.support import live_helpers
from typer.testing import CliRunner

from dubbed_video_downloader import core, doctor, languages
from dubbed_video_downloader.cli import app
from dubbed_video_downloader.yt_dlp_types import InfoDict

pytestmark = pytest.mark.live


def test_live_doctor_preflight(live_doctor_checks: list[doctor.CheckResult]) -> None:
    failed = [check for check in live_doctor_checks if not check.ok]
    assert not failed, "Live integration preflight failed: " + ", ".join(
        f"{check.name} ({check.detail})" for check in failed
    )


def test_live_get_video_info(live_test_url: str, live_video_info: InfoDict) -> None:
    info = core.get_video_info(live_test_url)
    assert info["id"] == live_video_info["id"]
    assert isinstance(info.get("formats"), list)
    assert info.get("title")


def test_live_audio_language_inventory(
    live_test_url: str,
    live_language_inventory: languages.AudioLanguageInventory,
) -> None:
    inventory = core.get_audio_language_inventory_for_url(live_test_url)
    assert inventory.langs
    assert len(languages.display_language_tags(inventory.langs)) >= (
        live_helpers.MIN_DUBBED_LANG_COUNT
    )


def test_live_get_quality_report(live_test_url: str, live_test_lang: str) -> None:
    report = core.get_quality_report(live_test_url, live_test_lang)
    assert report.resolved_lang
    assert report.video_qualities
    assert report.audio_qualities
    assert live_test_lang in report.available_langs or report.resolved_lang in (
        report.available_langs
    )


def test_live_plan_download(
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
    assert plan.resolved_lang
    assert plan.output_path.parent.as_posix().startswith(live_output_dir.as_posix())
    assert live_test_lang in plan.output_path.as_posix()
    assert not plan.output_exists


def test_live_cli_langs(
    live_test_url: str,
    live_test_lang: str,
    live_cli_env: dict[str, str],
    cli_runner: CliRunner,
) -> None:
    result = cli_runner.invoke(app, ["langs", live_test_url], env=live_cli_env)
    assert result.exit_code == 0, result.output
    assert live_test_lang in result.output


def test_live_cli_qualities(
    live_test_url: str,
    live_test_lang: str,
    live_cli_env: dict[str, str],
    cli_runner: CliRunner,
) -> None:
    result = cli_runner.invoke(
        app,
        ["qualities", live_test_url, "--lang", live_test_lang],
        env=live_cli_env,
    )
    assert result.exit_code == 0, result.output
    assert "Video qualities" in result.output or "video" in result.output.lower()


def test_live_cli_download_dry_run(
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
            "--dry-run",
            "--video-quality",
            "low",
            "--audio-quality",
            "low",
        ],
        env=live_cli_env,
    )
    assert result.exit_code == 0, result.output
    assert "dry run" in result.output.lower() or "Dry run" in result.output
