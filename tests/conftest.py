from __future__ import annotations

import contextlib
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from dubbed_video_downloader import core
from tests.support.network_guard import install_network_guard


@pytest.fixture(scope="session", autouse=True)
def _network_guard() -> None:
    install_network_guard()


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


def expected_config_yaml(**overrides: str) -> str:
    values = {
        "output_dir": "~/Downloads/dbdvdl-output",
        "ffmpeg_path": "ffmpeg",
        "default_lang": "en",
        "default_download_mode": "video",
        "default_video_quality": "best",
        "default_audio_quality": "best",
        "retry_on_network_failure": "3",
        "default_exists_behavior": "skip",
        "ask_for_disk_usage": "false",
    }
    values.update(overrides)
    return (
        f"output_dir: {values['output_dir']}\n"
        f"ffmpeg_path: {values['ffmpeg_path']}\n"
        f"default_lang: {values['default_lang']}\n"
        f"default_download_mode: {values['default_download_mode']}\n"
        f"default_video_quality: {values['default_video_quality']}\n"
        f"default_audio_quality: {values['default_audio_quality']}\n"
        f"retry_on_network_failure: {values['retry_on_network_failure']}\n"
        f"default_exists_behavior: {values['default_exists_behavior']}\n"
        f"ask_for_disk_usage: {values['ask_for_disk_usage']}\n"
    )


def download_result_with_file(
    output_path: Path,
    *,
    size_bytes: int = 0,
) -> core.DownloadResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if size_bytes:
        output_path.write_bytes(b"x" * size_bytes)
    else:
        output_path.touch()
    return core.DownloadResult(output_path=output_path)


def patch_successful_staged_finalization():
    return patch(
        "dubbed_video_downloader.core._finalize_staged_download",
        return_value=core.DownloadStatus.DOWNLOADED,
    )


@pytest.fixture
def staged_finalization_patch() -> Iterator[None]:
    with patch_successful_staged_finalization():
        yield


def assume_cross_filesystem_temp_roots() -> tuple[Path, Path]:
    output_root = Path("/tmp")
    redirected_root = Path("/dev/shm")
    if not output_root.is_dir() or not redirected_root.is_dir():
        pytest.skip("/tmp and /dev/shm are required for this regression test")
    if output_root.stat().st_dev == redirected_root.stat().st_dev:
        pytest.skip("/tmp and /dev/shm are on the same filesystem")
    return output_root, redirected_root


def assume_atomic_no_clobber_publish_supported(directory: Path) -> None:
    source_path = directory / "no-clobber-source.tmp"
    destination_path = directory / "no-clobber-destination.tmp"
    source_path.write_text("probe", encoding="utf-8")
    try:
        core._publish_file_no_clobber(source_path, destination_path)
    except core._AtomicNoClobberPublishUnsupportedError as exc:
        pytest.skip(str(exc))
    finally:
        with contextlib.suppress(FileNotFoundError, OSError):
            source_path.unlink()
        with contextlib.suppress(FileNotFoundError, OSError):
            destination_path.unlink()
