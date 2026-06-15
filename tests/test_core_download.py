from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from yt_dlp.utils import YoutubeDLError

from dubbed_video_downloader import core, errors
from tests.conftest import patch_successful_staged_finalization


def test_download_approval_callback_runs_before_media_download(tmp_path: Path) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    approved_plans: list[core.DownloadPlan] = []
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

        def approve(plan: core.DownloadPlan) -> bool:
            approved_plans.append(plan)
            youtube_dl.assert_not_called()
            return True

        ydl = youtube_dl.return_value.__enter__.return_value
        result = core.download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=Path(tmpdir),
            approval_callback=approve,
        )
    assert result.status == core.DownloadStatus.DOWNLOADED
    assert len(approved_plans) == 1
    assert approved_plans[0].output_path == output_path
    ydl.download.assert_called_once_with(["https://www.youtube.com/watch?v=EXAMPLE"])


def test_download_skip_if_output_appears_during_approval(tmp_path: Path) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    output_path = tmp_path / "tr" / "A_Title" / "A_Title.mkv"

    def approve(plan: core.DownloadPlan) -> bool:
        assert plan.output_path == output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("created during approval", encoding="utf-8")
        return True

    with (
        patch("dubbed_video_downloader.core.get_video_info", return_value=info),
        patch(
            "dubbed_video_downloader.core._planned_output_path",
            return_value=output_path,
        ),
        patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl,
    ):
        result = core.download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=tmp_path,
            exists_behavior=core.FileExistsBehavior.SKIP,
            approval_callback=approve,
        )

    assert result.status == core.DownloadStatus.SKIPPED
    assert result.output_path == output_path
    youtube_dl.assert_not_called()


def test_download_fail_if_output_appears_during_approval(tmp_path: Path) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    output_path = tmp_path / "tr" / "A_Title" / "A_Title.mkv"

    def approve(plan: core.DownloadPlan) -> bool:
        assert plan.output_path == output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("created during approval", encoding="utf-8")
        return True

    with (
        patch("dubbed_video_downloader.core.get_video_info", return_value=info),
        patch(
            "dubbed_video_downloader.core._planned_output_path",
            return_value=output_path,
        ),
        patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl,
        pytest.raises(errors.DownloadError, match="Output already exists"),
    ):
        core.download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=tmp_path,
            exists_behavior=core.FileExistsBehavior.FAIL,
            approval_callback=approve,
        )

    youtube_dl.assert_not_called()


def test_download_overwrite_if_output_appears_during_approval(tmp_path: Path) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    output_path = tmp_path / "tr" / "A_Title" / "A_Title.mkv"

    def approve(plan: core.DownloadPlan) -> bool:
        assert plan.output_path == output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("created during approval", encoding="utf-8")
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
        ydl = youtube_dl.return_value.__enter__.return_value
        result = core.download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=tmp_path,
            exists_behavior=core.FileExistsBehavior.OVERWRITE,
            approval_callback=approve,
        )

    assert result.status == core.DownloadStatus.DOWNLOADED
    ydl.download.assert_called_once_with(["https://www.youtube.com/watch?v=EXAMPLE"])


def test_download_audio_mode_does_not_report_merging_from_postprocessor_hook(
    tmp_path: Path,
) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    stages: list[core.DownloadStage] = []
    tmpdir = tmp_path
    output_path = Path(tmpdir) / "tr" / "A_Title" / "A_Title.webm"
    with (
        patch("dubbed_video_downloader.core.get_video_info", return_value=info),
        patch(
            "dubbed_video_downloader.core._planned_output_path",
            return_value=output_path,
        ),
        patch_successful_staged_finalization(),
        patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl,
    ):
        core.download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            download_mode=core.DownloadMode.AUDIO,
            output_dir=Path(tmpdir),
            stage_callback=stages.append,
        )
    opts = youtube_dl.call_args.args[0]
    stages.clear()
    opts["postprocessor_hooks"][0]({"status": "started"})
    assert stages == []


def test_download_audio_mode_uses_audio_only_selector(tmp_path: Path) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    tmpdir = tmp_path
    output_path = Path(tmpdir) / "tr" / "A_Title" / "A_Title.webm"
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
        core.download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            download_mode=core.DownloadMode.AUDIO,
            output_dir=Path(tmpdir),
        )
    opts = youtube_dl.call_args.args[0]
    assert opts["format"] == 'bestaudio[language="tr"]'
    assert "merge_output_format" not in opts
    ydl.download.assert_called_once_with(["https://www.youtube.com/watch?v=EXAMPLE"])


def test_download_cleans_staging_on_keyboard_interrupt(tmp_path: Path) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    output_path = output_dir / "tr" / "A_Title" / "A_Title.mkv"
    staging_output_dir = output_dir / "tmp" / ".incomplete" / "run"
    staged_part_path = staging_output_dir / "tr" / "A_Title" / "A_Title.mkv.part"

    def interrupt_download(urls: list[str]) -> None:
        staged_part_path.parent.mkdir(parents=True)
        staged_part_path.write_text("partial", encoding="utf-8")
        raise KeyboardInterrupt

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
        ydl.download.side_effect = interrupt_download
        with pytest.raises(KeyboardInterrupt):
            core.download(
                url="https://www.youtube.com/watch?v=EXAMPLE",
                lang="tr",
                output_dir=output_dir,
            )
    assert not output_path.exists()
    assert not staging_output_dir.exists()


def test_download_cleans_staging_when_ytdlp_download_fails(tmp_path: Path) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    output_path = output_dir / "tr" / "A_Title" / "A_Title.mkv"
    staging_output_dir = output_dir / "tmp" / ".incomplete" / "run"
    staged_part_path = staging_output_dir / "tr" / "A_Title" / "A_Title.mkv.part"

    def fail_download(urls: list[str]) -> None:
        staged_part_path.parent.mkdir(parents=True)
        staged_part_path.write_text("partial", encoding="utf-8")
        raise YoutubeDLError("download failed")

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
        ydl.download.side_effect = fail_download
        with pytest.raises(errors.DownloadError):
            core.download(
                url="https://www.youtube.com/watch?v=EXAMPLE",
                lang="tr",
                output_dir=output_dir,
            )
    assert not output_path.exists()
    assert not staging_output_dir.exists()


def test_download_declined_approval_cancels_without_downloading(tmp_path: Path) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    approved_plans: list[core.DownloadPlan] = []
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

        def decline(plan: core.DownloadPlan) -> bool:
            approved_plans.append(plan)
            return False

        result = core.download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=Path(tmpdir),
            approval_callback=decline,
        )
    assert result.status == core.DownloadStatus.CANCELLED
    assert result.output_path == output_path
    assert len(approved_plans) == 1
    youtube_dl.assert_not_called()


def test_download_enables_debug_ytdlp_output(tmp_path: Path) -> None:
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
        core.download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=Path(tmpdir),
            debug=True,
        )
    opts = youtube_dl.call_args.args[0]
    assert not opts["quiet"]
    assert not opts["no_warnings"]
    assert opts["verbose"]


def test_download_enables_verbose_ytdlp_output_without_debug(tmp_path: Path) -> None:
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
        core.download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=Path(tmpdir),
            verbose=True,
        )
    opts = youtube_dl.call_args.args[0]
    assert not opts["quiet"]
    assert not opts["no_warnings"]
    assert not opts["verbose"]


def test_download_fails_when_completed_staged_output_is_missing(tmp_path: Path) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    output_path = output_dir / "tr" / "A_Title" / "A_Title.mkv"
    staging_output_dir = output_dir / "tmp" / ".incomplete" / "run"
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
        patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL"),
        pytest.raises(errors.DownloadError) as context,
    ):
        core.download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=output_dir,
        )
    assert "Completed staged download is missing" in str(context.value)
    assert not staging_output_dir.exists()


def test_download_moves_completed_staged_file_to_final_output(tmp_path: Path) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    tmpdir = tmp_path
    output_dir = Path(tmpdir)
    output_path = output_dir / "tr" / "A_Title" / "A_Title.mkv"
    staging_output_dir = output_dir / "tmp" / ".incomplete" / "run"
    staged_output_path = staging_output_dir / "tr" / "A_Title" / "A_Title.mkv"

    def download_to_staging(urls: list[str]) -> None:
        staged_output_path.parent.mkdir(parents=True)
        staged_output_path.write_text("downloaded media", encoding="utf-8")

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
        ydl.download.side_effect = download_to_staging
        result = core.download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=output_dir,
        )
    assert result.status == core.DownloadStatus.DOWNLOADED
    assert output_path.read_text(encoding="utf-8") == "downloaded media"
    assert not staging_output_dir.exists()
    opts = youtube_dl.call_args.args[0]
    assert str(opts["outtmpl"]).startswith(str(staging_output_dir))
    assert not opts["continuedl"]


def test_download_progress_hook_invokes_progress_callback(tmp_path: Path) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    progress_updates: list[core.DownloadProgress] = []
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
        core.download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=Path(tmpdir),
            progress_callback=progress_updates.append,
        )
    opts = youtube_dl.call_args.args[0]
    opts["progress_hooks"][0](
        {
            "status": "downloading",
            "downloaded_bytes": 128449230,
            "total_bytes": 988479000,
            "speed": 4500000,
            "eta": 3897,
        }
    )
    assert len(progress_updates) == 1
    assert progress_updates[0].speed_bytes_per_sec == 4500000
    assert progress_updates[0].eta_seconds == 3897
    assert progress_updates[0].percent == pytest.approx(12.995, abs=0.01)


def test_download_rejects_symlinked_incomplete_root_before_downloading(
    tmp_path: Path,
) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    tmpdir = tmp_path
    root_dir = Path(tmpdir)
    output_dir = root_dir / "out"
    output_path = output_dir / "tr" / "A_Title" / "A_Title.mkv"
    outside_dir = root_dir / "outside"
    incomplete_dir = output_dir / "tmp" / ".incomplete"
    outside_dir.mkdir()
    incomplete_dir.parent.mkdir(parents=True)
    try:
        incomplete_dir.symlink_to(outside_dir, target_is_directory=True)
    except (NotImplementedError, OSError):
        pytest.skip("symlinks not supported on this platform")
    with (
        patch("dubbed_video_downloader.core.get_video_info", return_value=info),
        patch(
            "dubbed_video_downloader.core._planned_output_path",
            return_value=output_path,
        ),
        patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl,
        pytest.raises(errors.DownloadError) as context,
    ):
        core.download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=output_dir,
        )
    assert isinstance(context.value.__cause__, core._UnsafeStagingPathError)
    assert "Refusing to use" in str(context.value)
    assert "Could not prepare output directory" not in str(context.value)
    youtube_dl.assert_not_called()


def test_download_rejects_symlinked_tmp_parent_before_downloading(
    tmp_path: Path,
) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    tmpdir = tmp_path
    root_dir = Path(tmpdir)
    output_dir = root_dir / "out"
    output_path = output_dir / "tr" / "A_Title" / "A_Title.mkv"
    outside_tmp_dir = root_dir / "outside-tmp"
    tmp_parent = output_dir / "tmp"
    output_dir.mkdir()
    outside_tmp_dir.mkdir()
    try:
        tmp_parent.symlink_to(outside_tmp_dir, target_is_directory=True)
    except (NotImplementedError, OSError):
        pytest.skip("symlinks not supported on this platform")
    with (
        patch("dubbed_video_downloader.core.get_video_info", return_value=info),
        patch(
            "dubbed_video_downloader.core._planned_output_path",
            return_value=output_path,
        ),
        patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl,
        pytest.raises(errors.DownloadError) as context,
    ):
        core.download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=output_dir,
        )
    assert isinstance(context.value.__cause__, core._UnsafeStagingPathError)
    assert "Refusing to use" in str(context.value)
    assert "Could not prepare output directory" not in str(context.value)
    youtube_dl.assert_not_called()


def test_download_reports_status_stages_for_successful_video_download(
    tmp_path: Path,
) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    stages: list[core.DownloadStage] = []
    tmpdir = tmp_path
    output_path = Path(tmpdir) / "tr" / "A_Title" / "A_Title.mkv"
    with (
        patch("dubbed_video_downloader.core.get_video_info", return_value=info),
        patch(
            "dubbed_video_downloader.core._planned_output_path",
            return_value=output_path,
        ),
        patch_successful_staged_finalization(),
        patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL"),
    ):
        core.download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=Path(tmpdir),
            stage_callback=stages.append,
        )
    assert stages == [
        core.DownloadStage.FETCHING_METADATA,
        core.DownloadStage.CHECKING_LANGUAGES,
        core.DownloadStage.SELECTING_QUALITIES,
        core.DownloadStage.PLANNING_OUTPUT,
        core.DownloadStage.PREPARING_OUTPUT_DIR,
        core.DownloadStage.DOWNLOADING_MEDIA,
        core.DownloadStage.FINALIZING_OUTPUT,
    ]


def test_download_suppresses_warnings_by_default(tmp_path: Path) -> None:
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
            retry_on_network_failure=2,
        )
    assert result.status == core.DownloadStatus.DOWNLOADED
    assert result.output_path == output_path
    opts = youtube_dl.call_args.args[0]
    assert opts["quiet"]
    assert opts["no_warnings"]
    assert not opts["verbose"]
    assert opts["noprogress"]
    assert opts["format"] == 'bv+bestaudio[language="tr"]'
    assert opts["merge_output_format"] == "mkv"
    assert opts["retries"] == 2
    assert opts["fragment_retries"] == 2
    assert opts["extractor_retries"] == 2
    assert "file_access_retries" not in opts
    assert not opts["overwrites"]
    assert not opts["continuedl"]
    assert not opts["nopart"]
    ydl.download.assert_called_once_with(["https://www.youtube.com/watch?v=EXAMPLE"])


def test_download_video_and_audio_quality_build_safe_selector(tmp_path: Path) -> None:
    info = {
        "title": "A Title",
        "formats": [
            {
                "format_id": "progressive-720",
                "vcodec": "avc1.64001f",
                "acodec": "mp4a.40.2",
                "height": 720,
            },
            {
                "format_id": "video-360",
                "vcodec": "vp9",
                "acodec": "none",
                "height": 360,
            },
            {
                "format_id": "video-720",
                "vcodec": "vp9",
                "acodec": "none",
                "height": 720,
            },
            {
                "format_id": "tr-audio-low",
                "vcodec": "none",
                "acodec": "opus",
                "language": "tr",
                "abr": 50,
            },
            {
                "format_id": "tr-audio-high",
                "vcodec": "none",
                "acodec": "opus",
                "language": "tr",
                "abr": 160,
            },
        ],
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
        core.download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=Path(tmpdir),
            video_quality="medium",
            audio_quality="low",
        )
    opts = youtube_dl.call_args.args[0]
    assert opts["format"] == 'bv[height=720]+bestaudio[format_id="tr-audio-low"]'
    ydl.download.assert_called_once_with(["https://www.youtube.com/watch?v=EXAMPLE"])


def test_download_wires_ytdlp_status_hooks(tmp_path: Path) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    stages: list[core.DownloadStage] = []
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
        core.download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=Path(tmpdir),
            stage_callback=stages.append,
        )
    opts = youtube_dl.call_args.args[0]
    assert len(opts["progress_hooks"]) == 1
    assert len(opts["postprocessor_hooks"]) == 1
    stages.clear()
    opts["progress_hooks"][0]({"status": "downloading"})
    opts["postprocessor_hooks"][0]({"status": "started"})
    assert stages == [
        core.DownloadStage.DOWNLOADING_MEDIA,
        core.DownloadStage.MERGING_MEDIA,
    ]


def test_download_wraps_output_directory_failures() -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    cause = OSError("permission denied")
    with (
        patch("dubbed_video_downloader.core.get_video_info", return_value=info),
        patch(
            "dubbed_video_downloader.core._planned_output_path",
            return_value=Path("/tmp/example/tr/A_Title/A_Title.mkv"),
        ),
        patch("dubbed_video_downloader.core.Path.mkdir", side_effect=cause),
        pytest.raises(errors.DownloadError) as context,
    ):
        core.download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=Path("/tmp/example"),
        )
    assert context.value.__cause__ is cause
    assert "Could not prepare output directory" in str(context.value)


def test_download_wraps_ytdlp_download_failures(tmp_path: Path) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    cause = YoutubeDLError("download failed")
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
        ydl.download.side_effect = cause
        with pytest.raises(errors.DownloadError) as context:
            core.download(
                url="https://www.youtube.com/watch?v=EXAMPLE",
                lang="tr",
                output_dir=Path(tmpdir),
            )
    assert context.value.__cause__ is cause
    assert "Could not download media" in str(context.value)
    assert "download failed" in str(context.value)


def test_parse_download_progress_parses_full_progress() -> None:
    progress = core._parse_download_progress(
        {
            "status": "downloading",
            "downloaded_bytes": 128449230,
            "total_bytes": 988479000,
            "speed": 4500000,
            "eta": 3897,
        }
    )
    assert progress is not None
    assert progress is not None
    assert progress.speed_bytes_per_sec == 4500000
    assert progress.eta_seconds == 3897
    assert progress.percent == pytest.approx(12.995, abs=0.01)


def test_parse_download_progress_returns_none_for_non_downloading_status() -> None:
    assert core._parse_download_progress({"status": "finished"}) is None


def test_parse_download_progress_returns_none_percent_when_total_unknown() -> None:
    progress = core._parse_download_progress(
        {"status": "downloading", "downloaded_bytes": 500}
    )
    assert progress is not None
    assert progress is not None
    assert progress.percent is None


def test_parse_download_progress_uses_total_bytes_estimate() -> None:
    progress = core._parse_download_progress(
        {"status": "downloading", "downloaded_bytes": 500, "total_bytes_estimate": 1000}
    )
    assert progress is not None
    assert progress is not None
    assert progress.percent == 50.0
