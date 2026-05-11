from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dubbed_video_downloader import core


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

    def test_get_video_info_enables_verbose_ytdlp_output(self) -> None:
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
        self.assertTrue(opts["verbose"])

    def test_plan_download_returns_output_preview_without_creating_directories(
        self,
    ) -> None:
        info = {
            "title": "A Title",
            "uploader": "Example Channel",
            "formats": [
                {
                    "vcodec": "none",
                    "acodec": "mp4a.40.2",
                    "language": "tr",
                },
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
                plan = core.plan_download(
                    url="https://www.youtube.com/watch?v=EXAMPLE",
                    lang="tr",
                    output_dir=output_dir,
                )

            self.assertFalse(output_dir.exists())

        self.assertEqual(plan.url, "https://www.youtube.com/watch?v=EXAMPLE")
        self.assertEqual(plan.lang, "tr")
        self.assertEqual(plan.title, "A Title")
        self.assertEqual(plan.uploader, "Example Channel")
        self.assertEqual(plan.available_langs, ("en", "tr"))
        self.assertEqual(
            plan.output_path,
            output_dir / "tr" / "Example_Channel" / "A_Title" / "A_Title.mkv",
        )

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
                with self.assertRaises(RuntimeError) as context:
                    core.plan_download(
                        url="https://www.youtube.com/watch?v=EXAMPLE",
                        lang="tr",
                        output_dir=output_dir,
                    )

            self.assertFalse(output_dir.exists())

        self.assertIn("Requested dub language not found", str(context.exception))

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
            with (
                patch("dubbed_video_downloader.core.get_video_info", return_value=info),
                patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl,
            ):
                ydl = youtube_dl.return_value.__enter__.return_value
                core.download(
                    url="https://www.youtube.com/watch?v=EXAMPLE",
                    lang="tr",
                    output_dir=Path(tmpdir),
                )

        opts = youtube_dl.call_args.args[0]
        self.assertTrue(opts["no_warnings"])
        self.assertFalse(opts["verbose"])
        ydl.download.assert_called_once_with(["https://www.youtube.com/watch?v=EXAMPLE"])

    def test_download_enables_verbose_ytdlp_output(self) -> None:
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
                core.download(
                    url="https://www.youtube.com/watch?v=EXAMPLE",
                    lang="tr",
                    output_dir=Path(tmpdir),
                    verbose=True,
                )

        opts = youtube_dl.call_args.args[0]
        self.assertFalse(opts["no_warnings"])
        self.assertTrue(opts["verbose"])


if __name__ == "__main__":
    unittest.main()
