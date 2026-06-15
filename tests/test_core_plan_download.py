from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from yt_dlp.utils import YoutubeDLError

from dubbed_video_downloader import core, errors, quality


def test_available_video_heights_ignore_progressive_formats() -> None:
    info = {
        "formats": [
            {
                "format_id": "progressive-720",
                "vcodec": "avc1.64001f",
                "acodec": "mp4a.40.2",
                "height": 720,
            },
            {
                "format_id": "video-480",
                "vcodec": "vp9",
                "acodec": "none",
                "height": 480,
            },
        ]
    }
    assert quality.get_available_video_heights(info) == (480,)


def test_plan_download_audio_medium_falls_back_when_bitrate_is_missing(
    tmp_path: Path,
) -> None:
    info = {
        "id": "example",
        "extractor": "youtube",
        "title": "A Title",
        "uploader": "Example Channel",
        "formats": [
            {
                "format_id": "tr-audio",
                "vcodec": "none",
                "acodec": "opus",
                "language": "tr",
                "ext": "webm",
                "url": "https://example.test/tr.webm",
            }
        ],
    }
    tmpdir = tmp_path
    output_dir = Path(tmpdir) / "planned-output"
    with patch("dubbed_video_downloader.core.get_video_info", return_value=info):
        plan = core.plan_download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            download_mode=core.DownloadMode.AUDIO,
            output_dir=output_dir,
            audio_quality="medium",
        )
    assert plan.audio_quality == "medium"
    assert plan.selected_audio_quality == "best"
    assert "bitrate metadata is unavailable" in plan.quality_notes[0]


def test_plan_download_audio_mode_uses_native_audio_extension(tmp_path: Path) -> None:
    info = {
        "id": "example",
        "extractor": "youtube",
        "title": "A Title",
        "uploader": "Example Channel",
        "formats": [
            {
                "format_id": "video",
                "vcodec": "vp9",
                "acodec": "none",
                "ext": "webm",
                "url": "https://example.test/video.webm",
                "tbr": 500,
            },
            {
                "format_id": "tr-audio-low",
                "vcodec": "none",
                "acodec": "mp4a.40.2",
                "language": "tr",
                "ext": "m4a",
                "url": "https://example.test/tr-low.m4a",
                "tbr": 50,
            },
            {
                "format_id": "tr-audio-high",
                "vcodec": "none",
                "acodec": "opus",
                "language": "tr",
                "ext": "webm",
                "url": "https://example.test/tr-high.webm",
                "tbr": 160,
            },
        ],
    }
    tmpdir = tmp_path
    output_dir = Path(tmpdir) / "planned-output"
    with patch("dubbed_video_downloader.core.get_video_info", return_value=info):
        plan = core.plan_download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            download_mode=core.DownloadMode.AUDIO,
            output_dir=output_dir,
        )
    assert not output_dir.exists()
    assert plan.download_mode == core.DownloadMode.AUDIO
    assert (
        plan.output_path
        == output_dir / "tr" / "Example_Channel" / "A_Title" / "A_Title.webm"
    )


def test_plan_download_estimates_video_size_from_selected_formats(
    tmp_path: Path,
) -> None:
    info = {
        "id": "example",
        "extractor": "youtube",
        "title": "A Title",
        "uploader": "Example Channel",
        "formats": [
            {
                "format_id": "video",
                "vcodec": "vp9",
                "acodec": "none",
                "ext": "webm",
                "url": "https://example.test/video.webm",
                "filesize": 100000000,
                "tbr": 500,
            },
            {
                "format_id": "tr-audio",
                "vcodec": "none",
                "acodec": "opus",
                "language": "tr",
                "ext": "webm",
                "url": "https://example.test/tr.webm",
                "filesize_approx": 39000000,
                "tbr": 128,
            },
        ],
    }
    tmpdir = tmp_path
    with patch("dubbed_video_downloader.core.get_video_info", return_value=info):
        plan = core.plan_download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=Path(tmpdir),
        )
    assert plan.estimated_size_bytes == 139000000


def test_plan_download_exact_video_quality_missing_fails_with_available_heights() -> (
    None
):
    info = {
        "title": "A Title",
        "formats": [
            {"vcodec": "vp9", "acodec": "none", "height": 360},
            {"vcodec": "vp9", "acodec": "none", "height": 720},
            {"vcodec": "none", "acodec": "opus", "language": "tr"},
        ],
    }
    with (
        patch("dubbed_video_downloader.core.get_video_info", return_value=info),
        pytest.raises(quality.QualityError) as context,
    ):
        core.plan_download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            video_quality="1080p",
        )
    assert "Requested video quality 1080p" in str(context.value)
    assert "360p, 720p" in str(context.value)


def test_plan_download_exact_video_quality_rejects_progressive_only_height() -> None:
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
                "format_id": "tr-audio",
                "vcodec": "none",
                "acodec": "opus",
                "language": "tr",
            },
        ],
    }
    with (
        patch("dubbed_video_downloader.core.get_video_info", return_value=info),
        pytest.raises(quality.QualityError) as context,
    ):
        core.plan_download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            video_quality="720p",
        )
    assert "No usable video qualities were found" in str(context.value)


def test_plan_download_matches_padded_metadata_language_tag(tmp_path: Path) -> None:
    info = {
        "id": "EXAMPLE",
        "extractor": "youtube",
        "title": "A Title",
        "uploader": "Example Channel",
        "formats": [
            {
                "format_id": "video",
                "vcodec": "vp9",
                "acodec": "none",
                "ext": "webm",
                "url": "https://example.test/video.webm",
                "height": 720,
                "tbr": 500,
            },
            {
                "format_id": "en-audio",
                "vcodec": "none",
                "acodec": "mp4a.40.2",
                "language": " en ",
                "ext": "m4a",
                "url": "https://example.test/en.m4a",
                "tbr": 128,
            },
        ],
    }
    tmpdir = tmp_path
    output_dir = Path(tmpdir) / "planned-output"
    with patch("dubbed_video_downloader.core.get_video_info", return_value=info):
        plan = core.plan_download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="en",
            output_dir=output_dir,
        )
    assert plan.lang == "en"
    assert plan.resolved_lang == " en "
    assert " en " in str(plan.output_path)


def test_plan_download_medium_video_ignores_progressive_heights(tmp_path: Path) -> None:
    info = {
        "id": "example",
        "extractor": "youtube",
        "title": "A Title",
        "uploader": "Example Channel",
        "formats": [
            {
                "format_id": "progressive-720",
                "vcodec": "avc1.64001f",
                "acodec": "mp4a.40.2",
                "height": 720,
                "ext": "mp4",
                "url": "https://example.test/progressive.mp4",
                "tbr": 1500,
            },
            {
                "format_id": "video-480",
                "vcodec": "vp9",
                "acodec": "none",
                "height": 480,
                "ext": "webm",
                "url": "https://example.test/video.webm",
                "tbr": 500,
            },
            {
                "format_id": "tr-audio",
                "vcodec": "none",
                "acodec": "opus",
                "language": "tr",
                "ext": "webm",
                "url": "https://example.test/tr.webm",
                "tbr": 128,
            },
        ],
    }
    tmpdir = tmp_path
    output_dir = Path(tmpdir) / "planned-output"
    with patch("dubbed_video_downloader.core.get_video_info", return_value=info):
        plan = core.plan_download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=output_dir,
            video_quality="medium",
        )
    assert plan.video_quality == "medium"
    assert plan.selected_video_quality == "480p"


def test_plan_download_medium_video_uses_single_available_height(
    tmp_path: Path,
) -> None:
    info = {
        "id": "example",
        "extractor": "youtube",
        "title": "A Title",
        "uploader": "Example Channel",
        "formats": [
            {
                "format_id": "video-480",
                "vcodec": "vp9",
                "acodec": "none",
                "height": 480,
                "ext": "webm",
                "url": "https://example.test/video.webm",
                "tbr": 500,
            },
            {
                "format_id": "tr-audio",
                "vcodec": "none",
                "acodec": "opus",
                "language": "tr",
                "ext": "webm",
                "url": "https://example.test/tr.webm",
                "tbr": 128,
            },
        ],
    }
    tmpdir = tmp_path
    output_dir = Path(tmpdir) / "planned-output"
    with patch("dubbed_video_downloader.core.get_video_info", return_value=info):
        plan = core.plan_download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=output_dir,
            video_quality="medium",
            audio_quality="low",
        )
    assert plan.video_quality == "medium"
    assert plan.selected_video_quality == "480p"
    assert plan.audio_quality == "low"
    assert plan.selected_audio_quality == "128k"


def test_plan_download_raises_download_error_when_output_path_is_missing(
    tmp_path: Path,
) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    tmpdir = tmp_path
    with (
        patch("dubbed_video_downloader.core.get_video_info", return_value=info),
        patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl,
        pytest.raises(errors.DownloadError) as context,
    ):
        ydl = youtube_dl.return_value.__enter__.return_value
        ydl.process_ie_result.return_value = info
        ydl.prepare_filename.return_value = ""
        core.plan_download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=Path(tmpdir),
        )
    assert "Could not determine planned output path" in str(context.value)


def test_plan_download_raises_when_requested_language_is_missing(
    tmp_path: Path,
) -> None:
    info = {
        "title": "A Title",
        "uploader": "Example Channel",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "en"}],
    }
    tmpdir = tmp_path
    output_dir = Path(tmpdir) / "planned-output"
    with (
        patch("dubbed_video_downloader.core.get_video_info", return_value=info),
        pytest.raises(errors.LanguageNotFoundError) as context,
    ):
        core.plan_download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=output_dir,
        )
    assert not output_dir.exists()
    assert "Requested dub language not found" in str(context.value)
    assert "Requested: tr" in str(context.value)
    assert "Available: en" in str(context.value)


def test_plan_download_reports_existing_output_state(tmp_path: Path) -> None:
    info = {
        "title": "A Title",
        "uploader": "Example Channel",
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
    ):
        plan = core.plan_download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=Path(tmpdir),
            exists_behavior=core.FileExistsBehavior.FAIL,
        )
    assert plan.output_path == output_path
    assert plan.output_exists
    assert plan.exists_behavior == core.FileExistsBehavior.FAIL


def test_plan_download_reports_unknown_size_when_selected_format_size_is_missing(
    tmp_path: Path,
) -> None:
    info = {
        "id": "example",
        "extractor": "youtube",
        "title": "A Title",
        "uploader": "Example Channel",
        "formats": [
            {
                "format_id": "video",
                "vcodec": "vp9",
                "acodec": "none",
                "ext": "webm",
                "url": "https://example.test/video.webm",
                "filesize": 100000000,
                "tbr": 500,
            },
            {
                "format_id": "tr-audio",
                "vcodec": "none",
                "acodec": "opus",
                "language": "tr",
                "ext": "webm",
                "url": "https://example.test/tr.webm",
                "tbr": 128,
            },
        ],
    }
    tmpdir = tmp_path
    with patch("dubbed_video_downloader.core.get_video_info", return_value=info):
        plan = core.plan_download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=Path(tmpdir),
        )
    assert plan.estimated_size_bytes is None


def test_plan_download_resolves_language_variants(tmp_path: Path) -> None:
    info = {
        "id": "EXAMPLE",
        "extractor": "youtube",
        "title": "A Title",
        "uploader": "Example Channel",
        "formats": [
            {
                "format_id": "video",
                "vcodec": "vp9",
                "acodec": "none",
                "ext": "webm",
                "url": "https://example.test/video.webm",
                "height": 720,
                "tbr": 500,
            },
            {
                "format_id": "en-us-audio",
                "vcodec": "none",
                "acodec": "mp4a.40.2",
                "language": "en-US",
                "ext": "m4a",
                "url": "https://example.test/en-us.m4a",
                "tbr": 128,
            },
        ],
    }
    tmpdir = tmp_path
    output_dir = Path(tmpdir) / "planned-output"
    with patch("dubbed_video_downloader.core.get_video_info", return_value=info):
        plan = core.plan_download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="en",
            output_dir=output_dir,
        )
    assert plan.lang == "en"
    assert plan.resolved_lang == "en-US"
    assert "en-US" in str(plan.output_path)


def test_plan_download_includes_mixed_case_audio_streams_for_resolved_language(
    tmp_path: Path,
) -> None:
    info = {
        "id": "EXAMPLE",
        "extractor": "youtube",
        "title": "A Title",
        "uploader": "Example Channel",
        "formats": [
            {
                "format_id": "video",
                "vcodec": "vp9",
                "acodec": "none",
                "ext": "webm",
                "url": "https://example.test/video.webm",
                "height": 720,
                "tbr": 500,
            },
            {
                "format_id": "en-us-high",
                "vcodec": "none",
                "acodec": "mp4a.40.2",
                "language": "en-US",
                "ext": "m4a",
                "url": "https://example.test/en-us-high.m4a",
                "abr": 160,
            },
            {
                "format_id": "en-us-low",
                "vcodec": "none",
                "acodec": "mp4a.40.2",
                "language": "en-us",
                "ext": "m4a",
                "url": "https://example.test/en-us-low.m4a",
                "abr": 64,
            },
        ],
    }
    output_dir = tmp_path / "planned-output"
    with patch("dubbed_video_downloader.core.get_video_info", return_value=info):
        plan = core.plan_download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="en",
            output_dir=output_dir,
        )
        report = core.get_quality_report(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="en",
        )

    assert plan.resolved_lang == "en-US"
    assert report.audio_qualities == ("64k", "160k")


def test_plan_download_returns_output_preview_without_creating_directories(
    tmp_path: Path,
) -> None:
    info = {
        "id": "example",
        "extractor": "youtube",
        "title": "A Title",
        "uploader": "Example Channel",
        "formats": [
            {
                "format_id": "video",
                "vcodec": "vp9",
                "acodec": "none",
                "ext": "webm",
                "url": "https://example.test/video.webm",
                "tbr": 500,
            },
            {
                "format_id": "tr-audio",
                "vcodec": "none",
                "acodec": "mp4a.40.2",
                "language": "tr",
                "ext": "m4a",
                "url": "https://example.test/tr.m4a",
                "tbr": 128,
            },
            {
                "format_id": "en-audio",
                "vcodec": "none",
                "acodec": "mp4a.40.2",
                "language": "en",
                "ext": "m4a",
                "url": "https://example.test/en.m4a",
                "tbr": 128,
            },
        ],
    }
    tmpdir = tmp_path
    output_dir = Path(tmpdir) / "planned-output"
    with patch("dubbed_video_downloader.core.get_video_info", return_value=info):
        plan = core.plan_download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=output_dir,
        )
    assert not output_dir.exists()
    assert plan.url == "https://www.youtube.com/watch?v=EXAMPLE"
    assert plan.lang == "tr"
    assert plan.download_mode == core.DownloadMode.VIDEO
    assert plan.title == "A Title"
    assert plan.uploader == "Example Channel"
    assert plan.available_langs == ("en", "tr")
    assert (
        plan.output_path
        == output_dir / "tr" / "Example_Channel" / "A_Title" / "A_Title.mkv"
    )


def test_plan_download_wraps_ytdlp_planning_failures(tmp_path: Path) -> None:
    info = {
        "title": "A Title",
        "formats": [{"vcodec": "none", "acodec": "mp4a.40.2", "language": "tr"}],
    }
    cause = YoutubeDLError("planning failed")
    tmpdir = tmp_path
    with (
        patch("dubbed_video_downloader.core.get_video_info", return_value=info),
        patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl,
        pytest.raises(errors.DownloadError) as context,
    ):
        ydl = youtube_dl.return_value.__enter__.return_value
        ydl.process_ie_result.side_effect = cause
        core.plan_download(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="tr",
            output_dir=Path(tmpdir),
        )
    assert context.value.__cause__ is cause
    assert "Could not plan download output" in str(context.value)
