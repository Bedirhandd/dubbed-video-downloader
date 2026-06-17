from __future__ import annotations

import os
import stat
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from dubbed_video_downloader import core
from dubbed_video_downloader.cli import app
from tests.conftest import download_result_with_file

VALID_URL = "https://www.youtube.com/watch?v=EXAMPLE"


def _write_minimal_config(home: Path, *, ffmpeg_path: str = "ffmpeg") -> None:
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\n"
        f"ffmpeg_path: {ffmpeg_path}\n"
        "default_lang: en\n",
        encoding="utf-8",
    )


def _write_executable(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
    path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)


@pytest.mark.parametrize("dry_run", [False, True])
def test_download_rejects_missing_absolute_ffmpeg_path_before_core_work(
    tmp_path: Path,
    cli_runner: CliRunner,
    dry_run: bool,
) -> None:
    home = Path(tmp_path)
    missing_ffmpeg = home / "bin" / "missing-ffmpeg"
    _write_minimal_config(home, ffmpeg_path=str(missing_ffmpeg))
    args = ["download", VALID_URL]
    if dry_run:
        args.append("--dry-run")
    with (
        patch("dubbed_video_downloader.cli.core.download") as download,
        patch("dubbed_video_downloader.cli.core.plan_download") as plan,
    ):
        result = cli_runner.invoke(app, args, env={"HOME": str(home)})
    assert result.exit_code == 1, result.output
    assert "Input error:" in result.output
    assert "does not exist" in result.output
    download.assert_not_called()
    plan.assert_not_called()


@pytest.mark.skipif(os.name == "nt", reason="POSIX executable bits are not modeled")
@pytest.mark.parametrize("dry_run", [False, True])
def test_download_rejects_non_executable_absolute_ffmpeg_path_before_core_work(
    tmp_path: Path,
    cli_runner: CliRunner,
    dry_run: bool,
) -> None:
    home = Path(tmp_path)
    ffmpeg_path = home / "bin" / "ffmpeg"
    ffmpeg_path.parent.mkdir(parents=True)
    ffmpeg_path.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
    ffmpeg_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    _write_minimal_config(home, ffmpeg_path=str(ffmpeg_path))
    args = ["download", VALID_URL]
    if dry_run:
        args.append("--dry-run")
    with (
        patch("dubbed_video_downloader.cli.core.download") as download,
        patch("dubbed_video_downloader.cli.core.plan_download") as plan,
    ):
        result = cli_runner.invoke(app, args, env={"HOME": str(home)})
    assert result.exit_code == 1, result.output
    assert "Input error:" in result.output
    assert "is not executable" in result.output
    download.assert_not_called()
    plan.assert_not_called()


@pytest.mark.parametrize("dry_run", [False, True])
def test_download_rejects_bare_ffmpeg_when_not_on_path_before_core_work(
    tmp_path: Path,
    cli_runner: CliRunner,
    dry_run: bool,
) -> None:
    home = Path(tmp_path)
    _write_minimal_config(home, ffmpeg_path="ffmpeg")
    args = ["download", VALID_URL]
    if dry_run:
        args.append("--dry-run")
    with (
        patch("dubbed_video_downloader.doctor.shutil.which", return_value=None),
        patch("dubbed_video_downloader.cli.core.download") as download,
        patch("dubbed_video_downloader.cli.core.plan_download") as plan,
    ):
        result = cli_runner.invoke(app, args, env={"HOME": str(home)})
    assert result.exit_code == 1, result.output
    assert "Input error:" in result.output
    assert "ffmpeg was not found on PATH" in result.output
    download.assert_not_called()
    plan.assert_not_called()


@pytest.mark.parametrize("dry_run", [False, True])
def test_download_accepts_bare_ffmpeg_on_path(
    tmp_path: Path,
    cli_runner: CliRunner,
    dry_run: bool,
) -> None:
    home = Path(tmp_path)
    _write_minimal_config(home, ffmpeg_path="ffmpeg")
    output_path = home / "Downloads" / "from-config" / "en" / "Title.mkv"
    args = ["download", VALID_URL]
    if dry_run:
        args.append("--dry-run")
    with (
        patch(
            "dubbed_video_downloader.doctor.shutil.which",
            return_value="/usr/bin/ffmpeg",
        ),
        patch("dubbed_video_downloader.cli.core.download") as download,
        patch(
            "dubbed_video_downloader.cli.core.plan_download",
            return_value=core.DownloadPlan(
                url=VALID_URL,
                lang="en",
                resolved_lang="en",
                title="Title",
                uploader="Channel",
                available_langs=("en",),
                output_path=output_path,
            ),
        ) as plan,
    ):
        if dry_run:
            result = cli_runner.invoke(app, args, env={"HOME": str(home)})
        else:
            download.return_value = download_result_with_file(output_path)
            result = cli_runner.invoke(app, args, env={"HOME": str(home)})
    assert result.exit_code == 0, result.output
    if dry_run:
        plan.assert_called_once()
        assert plan.call_args.kwargs["ffmpeg_path"] is None
    else:
        download.assert_called_once()
        assert download.call_args.kwargs["ffmpeg_path"] is None


def test_download_accepts_valid_absolute_executable_ffmpeg_path(
    tmp_path: Path,
    cli_runner: CliRunner,
) -> None:
    home = Path(tmp_path)
    ffmpeg_path = home / "bin" / "ffmpeg"
    _write_executable(ffmpeg_path)
    _write_minimal_config(home, ffmpeg_path=str(ffmpeg_path))
    output_path = home / "Downloads" / "from-config" / "en" / "Title.mkv"
    with patch("dubbed_video_downloader.cli.core.download") as download:
        download.return_value = download_result_with_file(output_path)
        result = cli_runner.invoke(
            app,
            ["download", VALID_URL],
            env={"HOME": str(home)},
        )
    assert result.exit_code == 0, result.output
    download.assert_called_once()
    assert download.call_args.kwargs["ffmpeg_path"] == str(ffmpeg_path)
