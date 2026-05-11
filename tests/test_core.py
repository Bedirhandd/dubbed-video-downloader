from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dubbed_video_downloader import core


class CoreTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
