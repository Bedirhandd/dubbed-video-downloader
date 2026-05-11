from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dubbed_video_downloader import config


class ConfigTests(unittest.TestCase):
    def test_missing_config_fails_with_init_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = Path(tmpdir) / "config.yaml"

            with self.assertRaises(config.ConfigError) as context:
                config.load_config(missing_path)

        self.assertIn("Run `dbdvdl init`", str(context.exception))

    def test_valid_config_loads_and_expands_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = home / "config.yaml"
            config_path.write_text(
                "output_dir: ~/Videos\nffmpeg_path: $HOME/bin/ffmpeg\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"HOME": str(home)}):
                loaded_config = config.load_config(config_path)

        self.assertEqual(loaded_config.output_dir, home / "Videos")
        self.assertEqual(loaded_config.ffmpeg_path, str(home / "bin" / "ffmpeg"))

    def test_unknown_keys_are_ignored(self) -> None:
        loaded_config = config.config_from_mapping(
            {
                "output_dir": "/tmp/dbdvdl-output",
                "ffmpeg_path": "ffmpeg",
                "future": "accepted",
            }
        )

        self.assertEqual(loaded_config.output_dir, Path("/tmp/dbdvdl-output"))
        self.assertEqual(loaded_config.ffmpeg_path, "ffmpeg")

    def test_missing_required_key_fails(self) -> None:
        with self.assertRaises(config.ConfigError) as context:
            config.config_from_mapping({"output_dir": "/tmp/dbdvdl-output"})

        self.assertIn("ffmpeg_path", str(context.exception))

    def test_wrong_value_type_fails(self) -> None:
        with self.assertRaises(config.ConfigError) as context:
            config.config_from_mapping(
                {
                    "output_dir": "/tmp/dbdvdl-output",
                    "ffmpeg_path": 123,
                }
            )

        self.assertIn("ffmpeg_path", str(context.exception))

    def test_relative_output_dir_fails(self) -> None:
        with self.assertRaises(config.ConfigError) as context:
            config.normalize_output_dir("Videos")

        self.assertIn("absolute path", str(context.exception))

    def test_relative_ffmpeg_path_fails(self) -> None:
        with self.assertRaises(config.ConfigError) as context:
            config.normalize_ffmpeg_path("bin/ffmpeg")

        self.assertIn("ffmpeg", str(context.exception))


if __name__ == "__main__":
    unittest.main()
