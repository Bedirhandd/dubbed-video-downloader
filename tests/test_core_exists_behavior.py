from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from dubbed_video_downloader import core, errors
from tests.conftest import patch_successful_staged_finalization


def test_download_fail_behavior_downloads_when_output_is_missing(
    tmp_path: Path,
) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    tmpdir = tmp_path
    output_path = Path(tmpdir) / "tr" / "A_Title" / "A_Title.mkv"
    with (
        patch("dubbed_video_downloader.core.get_video_info", return_value=info),
        patch(
            "dubbed_video_downloader.core._planned_output_path",
            return_value=output_path,
        ),
        patch_successful_staged_finalization(),
        patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl,
    ):
        ydl = youtube_dl.return_value.__enter__.return_value
        result = core.download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=Path(tmpdir),
            exists_behavior=core.FileExistsBehavior.FAIL,
        )
    assert result.status == core.DownloadStatus.DOWNLOADED
    opts = youtube_dl.call_args.args[0]
    assert not opts["overwrites"]
    ydl.download.assert_called_once_with(["https://www.youtube.com/watch?v=EXAMPLE"])


def test_download_fail_existing_raises_without_downloading(tmp_path: Path) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    tmpdir = tmp_path
    output_path = Path(tmpdir) / "tr" / "A_Title" / "A_Title.mkv"
    output_path.parent.mkdir(parents=True)
    output_path.write_text("already downloaded", encoding="utf-8")
    with (
        patch("dubbed_video_downloader.core.get_video_info", return_value=info),
        patch(
            "dubbed_video_downloader.core._planned_output_path",
            return_value=output_path,
        ),
        patch_successful_staged_finalization(),
        patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl,
        pytest.raises(errors.DownloadError) as context,
    ):
        core.download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=Path(tmpdir),
            exists_behavior=core.FileExistsBehavior.FAIL,
        )
    assert "Output already exists" in str(context.value)
    youtube_dl.assert_not_called()


def test_download_fail_finalization_race_reports_existing_final_output(
    tmp_path: Path,
) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    output_path = output_dir / "tr" / "A_Title" / "A_Title.mkv"
    staging_output_dir = output_dir / "tmp" / ".incomplete" / "run"
    staged_output_path = staging_output_dir / "tr" / "A_Title" / "A_Title.mkv"
    original_link = core.os.link

    def download_to_staging(urls: list[str]) -> None:
        staged_output_path.parent.mkdir(parents=True)
        staged_output_path.write_text("downloaded media", encoding="utf-8")

    def create_output_before_link(src, dst) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("external media", encoding="utf-8")
        original_link(src, dst)

    with (
        patch("dubbed_video_downloader.core.get_video_info", return_value=info),
        patch(
            "dubbed_video_downloader.core._planned_output_path",
            return_value=output_path,
        ),
        patch(
            "dubbed_video_downloader.core._new_staging_output_dir",
            return_value=staging_output_dir,
        ),
        patch(
            "dubbed_video_downloader.core.os.link",
            side_effect=create_output_before_link,
        ),
        patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl,
    ):
        ydl = youtube_dl.return_value.__enter__.return_value
        ydl.download.side_effect = download_to_staging
        with pytest.raises(errors.DownloadError) as context:
            core.download(
                url="https://www.youtube.com/watch?v=EXAMPLE",
                lang="tr",
                output_dir=output_dir,
                exists_behavior=core.FileExistsBehavior.FAIL,
            )
    assert "Output already exists" in str(context.value)
    assert output_path.read_text(encoding="utf-8") == "external media"
    assert not staging_output_dir.exists()


def test_download_fail_race_reports_existing_final_output(tmp_path: Path) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    output_path = output_dir / "tr" / "A_Title" / "A_Title.mkv"
    staging_output_dir = output_dir / "tmp" / ".incomplete" / "run"
    staged_output_path = staging_output_dir / "tr" / "A_Title" / "A_Title.mkv"

    def download_while_output_appears(urls: list[str]) -> None:
        staged_output_path.parent.mkdir(parents=True)
        staged_output_path.write_text("downloaded media", encoding="utf-8")
        output_path.parent.mkdir(parents=True)
        output_path.write_text("external media", encoding="utf-8")

    with (
        patch("dubbed_video_downloader.core.get_video_info", return_value=info),
        patch(
            "dubbed_video_downloader.core._planned_output_path",
            return_value=output_path,
        ),
        patch(
            "dubbed_video_downloader.core._new_staging_output_dir",
            return_value=staging_output_dir,
        ),
        patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl,
    ):
        ydl = youtube_dl.return_value.__enter__.return_value
        ydl.download.side_effect = download_while_output_appears
        with pytest.raises(errors.DownloadError) as context:
            core.download(
                url="https://www.youtube.com/watch?v=EXAMPLE",
                lang="tr",
                output_dir=output_dir,
                exists_behavior=core.FileExistsBehavior.FAIL,
            )
    assert "Output already exists" in str(context.value)
    assert output_path.read_text(encoding="utf-8") == "external media"
    assert not staging_output_dir.exists()


def test_download_overwrite_existing_passes_force_overwrite_to_ytdlp(
    tmp_path: Path,
) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    tmpdir = tmp_path
    output_path = Path(tmpdir) / "tr" / "A_Title" / "A_Title.mkv"
    output_path.parent.mkdir(parents=True)
    output_path.write_text("already downloaded", encoding="utf-8")
    with (
        patch("dubbed_video_downloader.core.get_video_info", return_value=info),
        patch(
            "dubbed_video_downloader.core._planned_output_path",
            return_value=output_path,
        ),
        patch_successful_staged_finalization(),
        patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl,
    ):
        ydl = youtube_dl.return_value.__enter__.return_value
        result = core.download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=Path(tmpdir),
            exists_behavior=core.FileExistsBehavior.OVERWRITE,
        )
    assert result.status == core.DownloadStatus.DOWNLOADED
    opts = youtube_dl.call_args.args[0]
    assert opts["overwrites"]
    assert not opts["continuedl"]
    ydl.download.assert_called_once_with(["https://www.youtube.com/watch?v=EXAMPLE"])


def test_download_skip_existing_reports_status_stage(tmp_path: Path) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    stages: list[core.DownloadStage] = []
    tmpdir = tmp_path
    output_path = Path(tmpdir) / "tr" / "A_Title" / "A_Title.mkv"
    output_path.parent.mkdir(parents=True)
    output_path.write_text("already downloaded", encoding="utf-8")
    with (
        patch("dubbed_video_downloader.core.get_video_info", return_value=info),
        patch(
            "dubbed_video_downloader.core._planned_output_path",
            return_value=output_path,
        ),
        patch_successful_staged_finalization(),
        patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl,
    ):
        result = core.download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=Path(tmpdir),
            exists_behavior=core.FileExistsBehavior.SKIP,
            stage_callback=stages.append,
        )
    assert result.status == core.DownloadStatus.SKIPPED
    assert core.DownloadStage.SKIPPING_EXISTING_OUTPUT in stages
    youtube_dl.assert_not_called()


def test_download_skip_existing_returns_skipped_without_downloading(
    tmp_path: Path,
) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    tmpdir = tmp_path
    output_path = Path(tmpdir) / "tr" / "A_Title" / "A_Title.mkv"
    output_path.parent.mkdir(parents=True)
    output_path.write_text("already downloaded", encoding="utf-8")
    approval_plans: list[core.DownloadPlan] = []

    def approve(plan: core.DownloadPlan) -> bool:
        approval_plans.append(plan)
        return True

    with (
        patch("dubbed_video_downloader.core.get_video_info", return_value=info),
        patch(
            "dubbed_video_downloader.core._planned_output_path",
            return_value=output_path,
        ),
        patch_successful_staged_finalization(),
        patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl,
    ):
        result = core.download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=Path(tmpdir),
            exists_behavior=core.FileExistsBehavior.SKIP,
            approval_callback=approve,
        )
    assert result.status == core.DownloadStatus.SKIPPED
    assert result.output_path == output_path
    assert approval_plans == []
    youtube_dl.assert_not_called()


def test_download_skip_finalization_race_preserves_existing_final_output(
    tmp_path: Path,
) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    output_path = output_dir / "tr" / "A_Title" / "A_Title.mkv"
    staging_output_dir = output_dir / "tmp" / ".incomplete" / "run"
    staged_output_path = staging_output_dir / "tr" / "A_Title" / "A_Title.mkv"
    original_link = core.os.link

    def download_to_staging(urls: list[str]) -> None:
        staged_output_path.parent.mkdir(parents=True)
        staged_output_path.write_text("downloaded media", encoding="utf-8")

    def create_output_before_link(src, dst) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("external media", encoding="utf-8")
        original_link(src, dst)

    with (
        patch("dubbed_video_downloader.core.get_video_info", return_value=info),
        patch(
            "dubbed_video_downloader.core._planned_output_path",
            return_value=output_path,
        ),
        patch(
            "dubbed_video_downloader.core._new_staging_output_dir",
            return_value=staging_output_dir,
        ),
        patch(
            "dubbed_video_downloader.core.os.link",
            side_effect=create_output_before_link,
        ),
        patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl,
    ):
        ydl = youtube_dl.return_value.__enter__.return_value
        ydl.download.side_effect = download_to_staging
        result = core.download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=output_dir,
            exists_behavior=core.FileExistsBehavior.SKIP,
        )
    assert result.status == core.DownloadStatus.SKIPPED
    assert output_path.read_text(encoding="utf-8") == "external media"
    assert not staging_output_dir.exists()


def test_download_skip_race_preserves_existing_final_output(tmp_path: Path) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    output_path = output_dir / "tr" / "A_Title" / "A_Title.mkv"
    staging_output_dir = output_dir / "tmp" / ".incomplete" / "run"
    staged_output_path = staging_output_dir / "tr" / "A_Title" / "A_Title.mkv"

    def download_while_output_appears(urls: list[str]) -> None:
        staged_output_path.parent.mkdir(parents=True)
        staged_output_path.write_text("downloaded media", encoding="utf-8")
        output_path.parent.mkdir(parents=True)
        output_path.write_text("external media", encoding="utf-8")

    with (
        patch("dubbed_video_downloader.core.get_video_info", return_value=info),
        patch(
            "dubbed_video_downloader.core._planned_output_path",
            return_value=output_path,
        ),
        patch(
            "dubbed_video_downloader.core._new_staging_output_dir",
            return_value=staging_output_dir,
        ),
        patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl,
    ):
        ydl = youtube_dl.return_value.__enter__.return_value
        ydl.download.side_effect = download_while_output_appears
        result = core.download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=output_dir,
            exists_behavior=core.FileExistsBehavior.SKIP,
        )
    assert result.status == core.DownloadStatus.SKIPPED
    assert output_path.read_text(encoding="utf-8") == "external media"
    assert not staging_output_dir.exists()


@pytest.mark.parametrize("exists_behavior", list(core.FileExistsBehavior))
def test_existing_directory_at_output_path_always_fails(
    tmp_path: Path, exists_behavior: core.FileExistsBehavior
) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    output_path = tmp_path / "tr" / "A_Title" / "A_Title.mkv"
    output_path.mkdir(parents=True)
    with (
        patch(
            "dubbed_video_downloader.core.get_video_info",
            return_value=info,
        ),
        patch(
            "dubbed_video_downloader.core._planned_output_path",
            return_value=output_path,
        ),
        pytest.raises(errors.DownloadError) as context,
    ):
        core.download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=tmp_path,
            exists_behavior=exists_behavior,
        )
    assert "not a file" in str(context.value)
