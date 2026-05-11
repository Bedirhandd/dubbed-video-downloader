from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from dubbed_video_downloader.cli import app


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_init_writes_default_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(app, ["init"], env={"HOME": tmpdir})
            config_path = (
                Path(tmpdir)
                / ".config"
                / "dubbed-video-downloader"
                / "config.yaml"
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertEqual(
                config_path.read_text(encoding="utf-8"),
                "output_dir: ~/Downloads/dbdvdl-output\nffmpeg_path: ffmpeg\n",
            )

    def test_init_refuses_overwrite_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            first = self.runner.invoke(app, ["init"], env={"HOME": tmpdir})
            second = self.runner.invoke(app, ["init"], env={"HOME": tmpdir})

        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(second.exit_code, 1, second.output)
        self.assertIn("--force", second.output)

    def test_download_requires_config_before_network_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("dubbed_video_downloader.cli.core.download") as download:
                result = self.runner.invoke(
                    app,
                    ["download", "https://www.youtube.com/watch?v=EXAMPLE"],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("dbdvdl init", result.output)
        download.assert_not_called()

    def test_download_uses_config_and_allows_cli_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\n",
                encoding="utf-8",
            )
            override_output = home / "Videos" / "override"
            override_ffmpeg = home / "bin" / "ffmpeg"

            with patch("dubbed_video_downloader.cli.core.download") as download:
                result = self.runner.invoke(
                    app,
                    [
                        "download",
                        "https://www.youtube.com/watch?v=EXAMPLE",
                        "--lang",
                        "en",
                        "--output-dir",
                        str(override_output),
                        "--ffmpeg-path",
                        str(override_ffmpeg),
                    ],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 0, result.output)
        download.assert_called_once_with(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="en",
            ffmpeg_path=str(override_ffmpeg),
            output_dir=override_output,
        )

    def test_langs_requires_config_before_network_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "dubbed_video_downloader.cli.core.get_available_audio_langs_for_url"
            ) as langs:
                result = self.runner.invoke(
                    app,
                    ["langs", "https://www.youtube.com/watch?v=EXAMPLE"],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("dbdvdl init", result.output)
        langs.assert_not_called()


if __name__ == "__main__":
    unittest.main()
