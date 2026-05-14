from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from yt_dlp.utils import YoutubeDLError

from dubbed_video_downloader import core
from dubbed_video_downloader import errors
from dubbed_video_downloader import quality


class CoreTests(unittest.TestCase):
    def test_get_video_info_suppresses_warnings_by_default(self) -> None:
        with patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl:
            ydl = youtube_dl.return_value.__enter__.return_value
            ydl.extract_info.return_value = {"formats": []}

            info = core.get_video_info("https://www.youtube.com/watch?v=EXAMPLE")

        self.assertEqual(info, {"formats": []})
        ydl.extract_info.assert_called_once_with(
            "https://www.youtube.com/watch?v=EXAMPLE",
            download=False,
        )
        opts = youtube_dl.call_args.args[0]
        self.assertTrue(opts["quiet"])
        self.assertTrue(opts["no_warnings"])
        self.assertFalse(opts["verbose"])
        self.assertEqual(opts["retries"], core.DEFAULT_RETRY_ON_NETWORK_FAILURE)
        self.assertEqual(opts["fragment_retries"], core.DEFAULT_RETRY_ON_NETWORK_FAILURE)
        self.assertEqual(opts["extractor_retries"], core.DEFAULT_RETRY_ON_NETWORK_FAILURE)
        self.assertNotIn("file_access_retries", opts)
        self.assertEqual(
            set(opts["retry_sleep_functions"]),
            {"http", "fragment", "extractor"},
        )
        self.assertTrue(callable(opts["retry_sleep_functions"]["http"]))

    def test_get_video_info_enables_verbose_ytdlp_output_without_debug(self) -> None:
        with patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl:
            ydl = youtube_dl.return_value.__enter__.return_value
            ydl.extract_info.return_value = {"formats": []}

            core.get_video_info(
                "https://www.youtube.com/watch?v=EXAMPLE",
                verbose=True,
            )

        opts = youtube_dl.call_args.args[0]
        self.assertFalse(opts["quiet"])
        self.assertFalse(opts["no_warnings"])
        self.assertFalse(opts["verbose"])

    def test_get_video_info_enables_debug_ytdlp_output(self) -> None:
        with patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl:
            ydl = youtube_dl.return_value.__enter__.return_value
            ydl.extract_info.return_value = {"formats": []}

            core.get_video_info(
                "https://www.youtube.com/watch?v=EXAMPLE",
                debug=True,
            )

        opts = youtube_dl.call_args.args[0]
        self.assertFalse(opts["quiet"])
        self.assertFalse(opts["no_warnings"])
        self.assertTrue(opts["verbose"])

    def test_get_video_info_uses_custom_network_retry_count(self) -> None:
        with patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl:
            ydl = youtube_dl.return_value.__enter__.return_value
            ydl.extract_info.return_value = {"formats": []}

            core.get_video_info(
                "https://www.youtube.com/watch?v=EXAMPLE",
                retry_on_network_failure=2,
            )

        opts = youtube_dl.call_args.args[0]
        self.assertEqual(opts["retries"], 2)
        self.assertEqual(opts["fragment_retries"], 2)
        self.assertEqual(opts["extractor_retries"], 2)

    def test_get_video_info_wraps_ytdlp_metadata_failures(self) -> None:
        cause = YoutubeDLError("metadata failed")
        with patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl:
            ydl = youtube_dl.return_value.__enter__.return_value
            ydl.extract_info.side_effect = cause

            with self.assertRaises(errors.MetadataExtractionError) as context:
                core.get_video_info("https://www.youtube.com/watch?v=EXAMPLE")

        self.assertIs(context.exception.__cause__, cause)
        self.assertIn("Could not extract video metadata", str(context.exception))
        self.assertIn("metadata failed", str(context.exception))

    def test_get_video_info_rejects_invalid_network_retry_count(self) -> None:
        with self.assertRaises(ValueError) as context:
            core.get_video_info(
                "https://www.youtube.com/watch?v=EXAMPLE",
                retry_on_network_failure=-1,
            )

        self.assertIn("retry_on_network_failure", str(context.exception))

    def test_plan_download_returns_output_preview_without_creating_directories(
        self,
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

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "planned-output"
            with patch("dubbed_video_downloader.core.get_video_info", return_value=info):
                plan = core.plan_download(
                    url="https://www.youtube.com/watch?v=EXAMPLE",
                    lang="tr",
                    output_dir=output_dir,
                )

            self.assertFalse(output_dir.exists())

        self.assertEqual(plan.url, "https://www.youtube.com/watch?v=EXAMPLE")
        self.assertEqual(plan.lang, "tr")
        self.assertEqual(plan.download_mode, core.DownloadMode.VIDEO)
        self.assertEqual(plan.title, "A Title")
        self.assertEqual(plan.uploader, "Example Channel")
        self.assertEqual(plan.available_langs, ("en", "tr"))
        self.assertEqual(
            plan.output_path,
            output_dir / "tr" / "Example_Channel" / "A_Title" / "A_Title.mkv",
        )

    def test_plan_download_audio_mode_uses_native_audio_extension(self) -> None:
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

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "planned-output"
            with patch("dubbed_video_downloader.core.get_video_info", return_value=info):
                plan = core.plan_download(
                    url="https://www.youtube.com/watch?v=EXAMPLE",
                    lang="tr",
                    download_mode=core.DownloadMode.AUDIO,
                    output_dir=output_dir,
                )

            self.assertFalse(output_dir.exists())

        self.assertEqual(plan.download_mode, core.DownloadMode.AUDIO)
        self.assertEqual(
            plan.output_path,
            output_dir / "tr" / "Example_Channel" / "A_Title" / "A_Title.webm",
        )

    def test_plan_download_medium_video_uses_single_available_height(self) -> None:
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

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "planned-output"
            with patch("dubbed_video_downloader.core.get_video_info", return_value=info):
                plan = core.plan_download(
                    url="https://www.youtube.com/watch?v=EXAMPLE",
                    lang="tr",
                    output_dir=output_dir,
                    video_quality="medium",
                    audio_quality="low",
                )

        self.assertEqual(plan.video_quality, "medium")
        self.assertEqual(plan.selected_video_quality, "480p")
        self.assertEqual(plan.audio_quality, "low")
        self.assertEqual(plan.selected_audio_quality, "128k")

    def test_available_video_heights_ignore_progressive_formats(self) -> None:
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
            ],
        }

        self.assertEqual(quality.get_available_video_heights(info), (480,))

    def test_plan_download_medium_video_ignores_progressive_heights(self) -> None:
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

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "planned-output"
            with patch("dubbed_video_downloader.core.get_video_info", return_value=info):
                plan = core.plan_download(
                    url="https://www.youtube.com/watch?v=EXAMPLE",
                    lang="tr",
                    output_dir=output_dir,
                    video_quality="medium",
                )

        self.assertEqual(plan.video_quality, "medium")
        self.assertEqual(plan.selected_video_quality, "480p")

    def test_plan_download_exact_video_quality_rejects_progressive_only_height(
        self,
    ) -> None:
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

        with patch("dubbed_video_downloader.core.get_video_info", return_value=info):
            with self.assertRaises(quality.QualityError) as context:
                core.plan_download(
                    url="https://www.youtube.com/watch?v=EXAMPLE",
                    lang="tr",
                    video_quality="720p",
                )

        self.assertIn("No usable video qualities were found", str(context.exception))

    def test_plan_download_exact_video_quality_missing_fails_with_available_heights(
        self,
    ) -> None:
        info = {
            "title": "A Title",
            "formats": [
                {
                    "vcodec": "vp9",
                    "acodec": "none",
                    "height": 360,
                },
                {
                    "vcodec": "vp9",
                    "acodec": "none",
                    "height": 720,
                },
                {
                    "vcodec": "none",
                    "acodec": "opus",
                    "language": "tr",
                },
            ],
        }

        with patch("dubbed_video_downloader.core.get_video_info", return_value=info):
            with self.assertRaises(quality.QualityError) as context:
                core.plan_download(
                    url="https://www.youtube.com/watch?v=EXAMPLE",
                    lang="tr",
                    video_quality="1080p",
                )

        self.assertIn("Requested video quality 1080p", str(context.exception))
        self.assertIn("360p, 720p", str(context.exception))

    def test_plan_download_audio_medium_falls_back_when_bitrate_is_missing(
        self,
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
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "planned-output"
            with patch("dubbed_video_downloader.core.get_video_info", return_value=info):
                plan = core.plan_download(
                    url="https://www.youtube.com/watch?v=EXAMPLE",
                    lang="tr",
                    download_mode=core.DownloadMode.AUDIO,
                    output_dir=output_dir,
                    audio_quality="medium",
                )

        self.assertEqual(plan.audio_quality, "medium")
        self.assertEqual(plan.selected_audio_quality, "best")
        self.assertIn("bitrate metadata is unavailable", plan.quality_notes[0])

    def test_plan_download_raises_when_requested_language_is_missing(self) -> None:
        info = {
            "title": "A Title",
            "uploader": "Example Channel",
            "formats": [
                {
                    "vcodec": "none",
                    "acodec": "mp4a.40.2",
                    "language": "en",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "planned-output"
            with patch("dubbed_video_downloader.core.get_video_info", return_value=info):
                with self.assertRaises(errors.LanguageNotFoundError) as context:
                    core.plan_download(
                        url="https://www.youtube.com/watch?v=EXAMPLE",
                        lang="tr",
                        output_dir=output_dir,
                    )

            self.assertFalse(output_dir.exists())

        self.assertIn("Requested dub language not found", str(context.exception))
        self.assertIn("Requested: tr", str(context.exception))
        self.assertIn("Available: en", str(context.exception))

    def test_download_suppresses_warnings_by_default(self) -> None:
        info = {
            "title": "A Title",
            "formats": [
                {
                    "vcodec": "none",
                    "acodec": "mp4a.40.2",
                    "language": "tr",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "tr" / "A_Title" / "A_Title.mkv"
            with (
                patch("dubbed_video_downloader.core.get_video_info", return_value=info),
                patch(
                    "dubbed_video_downloader.core._planned_output_path",
                    return_value=output_path,
                ),
                patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl,
            ):
                ydl = youtube_dl.return_value.__enter__.return_value
                result = core.download(
                    url="https://www.youtube.com/watch?v=EXAMPLE",
                    lang="tr",
                    output_dir=Path(tmpdir),
                    retry_on_network_failure=2,
                )

        self.assertEqual(result.status, core.DownloadStatus.DOWNLOADED)
        self.assertEqual(result.output_path, output_path)
        opts = youtube_dl.call_args.args[0]
        self.assertTrue(opts["quiet"])
        self.assertTrue(opts["no_warnings"])
        self.assertFalse(opts["verbose"])
        self.assertEqual(opts["format"], 'bv+bestaudio[language="tr"]')
        self.assertEqual(opts["merge_output_format"], "mkv")
        self.assertEqual(opts["retries"], 2)
        self.assertEqual(opts["fragment_retries"], 2)
        self.assertEqual(opts["extractor_retries"], 2)
        self.assertNotIn("file_access_retries", opts)
        self.assertFalse(opts["overwrites"])
        ydl.download.assert_called_once_with(["https://www.youtube.com/watch?v=EXAMPLE"])

    def test_download_audio_mode_uses_audio_only_selector(self) -> None:
        info = {
            "title": "A Title",
            "formats": [
                {
                    "vcodec": "none",
                    "acodec": "mp4a.40.2",
                    "language": "tr",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "tr" / "A_Title" / "A_Title.webm"
            with (
                patch("dubbed_video_downloader.core.get_video_info", return_value=info),
                patch(
                    "dubbed_video_downloader.core._planned_output_path",
                    return_value=output_path,
                ),
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
        self.assertEqual(opts["format"], 'bestaudio[language="tr"]')
        self.assertNotIn("merge_output_format", opts)
        ydl.download.assert_called_once_with(["https://www.youtube.com/watch?v=EXAMPLE"])

    def test_download_video_and_audio_quality_build_safe_selector(self) -> None:
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

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "tr" / "A_Title" / "A_Title.mkv"
            with (
                patch("dubbed_video_downloader.core.get_video_info", return_value=info),
                patch(
                    "dubbed_video_downloader.core._planned_output_path",
                    return_value=output_path,
                ),
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
        self.assertEqual(
            opts["format"],
            'bv[height=720]+bestaudio[language="tr"][format_id="tr-audio-low"]',
        )
        ydl.download.assert_called_once_with(["https://www.youtube.com/watch?v=EXAMPLE"])

    def test_download_enables_verbose_ytdlp_output_without_debug(self) -> None:
        info = {
            "title": "A Title",
            "formats": [
                {
                    "vcodec": "none",
                    "acodec": "mp4a.40.2",
                    "language": "tr",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "tr" / "A_Title" / "A_Title.mkv"
            with (
                patch("dubbed_video_downloader.core.get_video_info", return_value=info),
                patch(
                    "dubbed_video_downloader.core._planned_output_path",
                    return_value=output_path,
                ),
                patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl,
            ):
                core.download(
                    url="https://www.youtube.com/watch?v=EXAMPLE",
                    lang="tr",
                    output_dir=Path(tmpdir),
                    verbose=True,
                )

        opts = youtube_dl.call_args.args[0]
        self.assertFalse(opts["quiet"])
        self.assertFalse(opts["no_warnings"])
        self.assertFalse(opts["verbose"])

    def test_download_enables_debug_ytdlp_output(self) -> None:
        info = {
            "title": "A Title",
            "formats": [
                {
                    "vcodec": "none",
                    "acodec": "mp4a.40.2",
                    "language": "tr",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "tr" / "A_Title" / "A_Title.mkv"
            with (
                patch("dubbed_video_downloader.core.get_video_info", return_value=info),
                patch(
                    "dubbed_video_downloader.core._planned_output_path",
                    return_value=output_path,
                ),
                patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl,
            ):
                core.download(
                    url="https://www.youtube.com/watch?v=EXAMPLE",
                    lang="tr",
                    output_dir=Path(tmpdir),
                    debug=True,
                )

        opts = youtube_dl.call_args.args[0]
        self.assertFalse(opts["quiet"])
        self.assertFalse(opts["no_warnings"])
        self.assertTrue(opts["verbose"])

    def test_download_wraps_output_directory_failures(self) -> None:
        info = {
            "title": "A Title",
            "formats": [
                {
                    "vcodec": "none",
                    "acodec": "mp4a.40.2",
                    "language": "tr",
                },
            ],
        }
        cause = OSError("permission denied")

        with (
            patch("dubbed_video_downloader.core.get_video_info", return_value=info),
            patch(
                "dubbed_video_downloader.core._planned_output_path",
                return_value=Path("/tmp/example/tr/A_Title/A_Title.mkv"),
            ),
            patch("dubbed_video_downloader.core.Path.mkdir", side_effect=cause),
        ):
            with self.assertRaises(errors.DownloadError) as context:
                core.download(
                    url="https://www.youtube.com/watch?v=EXAMPLE",
                    lang="tr",
                    output_dir=Path("/tmp/example"),
                )

        self.assertIs(context.exception.__cause__, cause)
        self.assertIn("Could not prepare output directory", str(context.exception))

    def test_download_wraps_ytdlp_download_failures(self) -> None:
        info = {
            "title": "A Title",
            "formats": [
                {
                    "vcodec": "none",
                    "acodec": "mp4a.40.2",
                    "language": "tr",
                },
            ],
        }
        cause = YoutubeDLError("download failed")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "tr" / "A_Title" / "A_Title.mkv"
            with (
                patch("dubbed_video_downloader.core.get_video_info", return_value=info),
                patch(
                    "dubbed_video_downloader.core._planned_output_path",
                    return_value=output_path,
                ),
                patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl,
            ):
                ydl = youtube_dl.return_value.__enter__.return_value
                ydl.download.side_effect = cause

                with self.assertRaises(errors.DownloadError) as context:
                    core.download(
                        url="https://www.youtube.com/watch?v=EXAMPLE",
                        lang="tr",
                        output_dir=Path(tmpdir),
                    )

        self.assertIs(context.exception.__cause__, cause)
        self.assertIn("Could not download media", str(context.exception))
        self.assertIn("download failed", str(context.exception))

    def test_download_skip_existing_returns_skipped_without_downloading(self) -> None:
        info = {
            "title": "A Title",
            "formats": [
                {
                    "vcodec": "none",
                    "acodec": "mp4a.40.2",
                    "language": "tr",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "tr" / "A_Title" / "A_Title.mkv"
            output_path.parent.mkdir(parents=True)
            output_path.write_text("already downloaded", encoding="utf-8")

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
                    output_dir=Path(tmpdir),
                    exists_behavior=core.FileExistsBehavior.SKIP,
                )

        self.assertEqual(result.status, core.DownloadStatus.SKIPPED)
        self.assertEqual(result.output_path, output_path)
        youtube_dl.assert_not_called()

    def test_download_fail_existing_raises_without_downloading(self) -> None:
        info = {
            "title": "A Title",
            "formats": [
                {
                    "vcodec": "none",
                    "acodec": "mp4a.40.2",
                    "language": "tr",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "tr" / "A_Title" / "A_Title.mkv"
            output_path.parent.mkdir(parents=True)
            output_path.write_text("already downloaded", encoding="utf-8")

            with (
                patch("dubbed_video_downloader.core.get_video_info", return_value=info),
                patch(
                    "dubbed_video_downloader.core._planned_output_path",
                    return_value=output_path,
                ),
                patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl,
            ):
                with self.assertRaises(errors.DownloadError) as context:
                    core.download(
                        url="https://www.youtube.com/watch?v=EXAMPLE",
                        lang="tr",
                        output_dir=Path(tmpdir),
                        exists_behavior=core.FileExistsBehavior.FAIL,
                    )

        self.assertIn("Output already exists", str(context.exception))
        youtube_dl.assert_not_called()

    def test_download_overwrite_existing_passes_force_overwrite_to_ytdlp(self) -> None:
        info = {
            "title": "A Title",
            "formats": [
                {
                    "vcodec": "none",
                    "acodec": "mp4a.40.2",
                    "language": "tr",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "tr" / "A_Title" / "A_Title.mkv"
            output_path.parent.mkdir(parents=True)
            output_path.write_text("already downloaded", encoding="utf-8")

            with (
                patch("dubbed_video_downloader.core.get_video_info", return_value=info),
                patch(
                    "dubbed_video_downloader.core._planned_output_path",
                    return_value=output_path,
                ),
                patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl,
            ):
                ydl = youtube_dl.return_value.__enter__.return_value
                result = core.download(
                    url="https://www.youtube.com/watch?v=EXAMPLE",
                    lang="tr",
                    output_dir=Path(tmpdir),
                    exists_behavior=core.FileExistsBehavior.OVERWRITE,
                )

        self.assertEqual(result.status, core.DownloadStatus.DOWNLOADED)
        opts = youtube_dl.call_args.args[0]
        self.assertTrue(opts["overwrites"])
        self.assertFalse(opts["continuedl"])
        ydl.download.assert_called_once_with(["https://www.youtube.com/watch?v=EXAMPLE"])

    def test_download_fail_behavior_downloads_when_output_is_missing(self) -> None:
        info = {
            "title": "A Title",
            "formats": [
                {
                    "vcodec": "none",
                    "acodec": "mp4a.40.2",
                    "language": "tr",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "tr" / "A_Title" / "A_Title.mkv"
            with (
                patch("dubbed_video_downloader.core.get_video_info", return_value=info),
                patch(
                    "dubbed_video_downloader.core._planned_output_path",
                    return_value=output_path,
                ),
                patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl,
            ):
                ydl = youtube_dl.return_value.__enter__.return_value
                result = core.download(
                    url="https://www.youtube.com/watch?v=EXAMPLE",
                    lang="tr",
                    output_dir=Path(tmpdir),
                    exists_behavior=core.FileExistsBehavior.FAIL,
                )

        self.assertEqual(result.status, core.DownloadStatus.DOWNLOADED)
        opts = youtube_dl.call_args.args[0]
        self.assertFalse(opts["overwrites"])
        ydl.download.assert_called_once_with(["https://www.youtube.com/watch?v=EXAMPLE"])

    def test_existing_directory_at_output_path_always_fails(self) -> None:
        info = {
            "title": "A Title",
            "formats": [
                {
                    "vcodec": "none",
                    "acodec": "mp4a.40.2",
                    "language": "tr",
                },
            ],
        }

        for exists_behavior in core.FileExistsBehavior:
            with self.subTest(exists_behavior=exists_behavior):
                with tempfile.TemporaryDirectory() as tmpdir:
                    output_path = Path(tmpdir) / "tr" / "A_Title" / "A_Title.mkv"
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
                    ):
                        with self.assertRaises(errors.DownloadError) as context:
                            core.download(
                                url="https://www.youtube.com/watch?v=EXAMPLE",
                                lang="tr",
                                output_dir=Path(tmpdir),
                                exists_behavior=exists_behavior,
                            )

                self.assertIn("not a file", str(context.exception))

    def test_plan_download_reports_existing_output_state(self) -> None:
        info = {
            "title": "A Title",
            "uploader": "Example Channel",
            "formats": [
                {
                    "vcodec": "none",
                    "acodec": "mp4a.40.2",
                    "language": "tr",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
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

        self.assertEqual(plan.output_path, output_path)
        self.assertTrue(plan.output_exists)
        self.assertEqual(plan.exists_behavior, core.FileExistsBehavior.FAIL)

    def test_plan_download_wraps_ytdlp_planning_failures(self) -> None:
        info = {
            "title": "A Title",
            "formats": [
                {
                    "vcodec": "none",
                    "acodec": "mp4a.40.2",
                    "language": "tr",
                },
            ],
        }
        cause = YoutubeDLError("planning failed")

        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch("dubbed_video_downloader.core.get_video_info", return_value=info),
                patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl,
            ):
                ydl = youtube_dl.return_value.__enter__.return_value
                ydl.process_ie_result.side_effect = cause

                with self.assertRaises(errors.DownloadError) as context:
                    core.plan_download(
                        url="https://www.youtube.com/watch?v=EXAMPLE",
                        lang="tr",
                        output_dir=Path(tmpdir),
                    )

        self.assertIs(context.exception.__cause__, cause)
        self.assertIn("Could not plan download output", str(context.exception))

    def test_plan_download_raises_download_error_when_output_path_is_missing(
        self,
    ) -> None:
        info = {
            "title": "A Title",
            "formats": [
                {
                    "vcodec": "none",
                    "acodec": "mp4a.40.2",
                    "language": "tr",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch("dubbed_video_downloader.core.get_video_info", return_value=info),
                patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl,
            ):
                ydl = youtube_dl.return_value.__enter__.return_value
                ydl.process_ie_result.return_value = info
                ydl.prepare_filename.return_value = ""

                with self.assertRaises(errors.DownloadError) as context:
                    core.plan_download(
                        url="https://www.youtube.com/watch?v=EXAMPLE",
                        lang="tr",
                        output_dir=Path(tmpdir),
                    )

        self.assertIn("Could not determine planned output path", str(context.exception))


if __name__ == "__main__":
    unittest.main()
