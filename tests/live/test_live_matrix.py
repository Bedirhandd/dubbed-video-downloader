from __future__ import annotations

from pathlib import Path

import pytest
from tests.support import live_helpers

from dubbed_video_downloader import core

pytestmark = [pytest.mark.live, pytest.mark.live_matrix]


@pytest.fixture(autouse=True)
def _require_live_matrix_enabled() -> None:
    live_helpers.require_live_matrix_enabled()


@pytest.mark.parametrize("audio_quality", live_helpers.AUDIO_MATRIX_QUALITIES)
def test_live_matrix_audio(
    live_test_url: str,
    live_test_lang: str,
    matrix_output_dir: Path,
    audio_quality: str,
) -> None:
    result = core.download(
        url=live_test_url,
        lang=live_test_lang,
        download_mode=core.DownloadMode.AUDIO,
        output_dir=matrix_output_dir,
        audio_quality=audio_quality,
        exists_behavior=core.FileExistsBehavior.OVERWRITE,
    )
    assert result.status == core.DownloadStatus.DOWNLOADED
    assert result.output_path is not None
    live_helpers.assert_output_under_language_dir(
        result.output_path,
        live_test_lang,
        matrix_output_dir,
    )


@pytest.mark.parametrize("video_quality", live_helpers.VIDEO_MATRIX_QUALITIES)
@pytest.mark.parametrize("audio_quality", live_helpers.AUDIO_MATRIX_QUALITIES)
def test_live_matrix_video(
    live_test_url: str,
    live_test_lang: str,
    matrix_output_dir: Path,
    video_quality: str,
    audio_quality: str,
) -> None:
    result = core.download(
        url=live_test_url,
        lang=live_test_lang,
        download_mode=core.DownloadMode.VIDEO,
        output_dir=matrix_output_dir,
        video_quality=video_quality,
        audio_quality=audio_quality,
        exists_behavior=core.FileExistsBehavior.OVERWRITE,
    )
    assert result.status == core.DownloadStatus.DOWNLOADED
    assert result.output_path is not None
    assert result.output_path.suffix == ".mkv"
    live_helpers.assert_output_under_language_dir(
        result.output_path,
        live_test_lang,
        matrix_output_dir,
    )
