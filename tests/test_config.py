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
                "output_dir: ~/Videos\n"
                "ffmpeg_path: $HOME/bin/ffmpeg\n"
                "default_lang: en\n"
                "default_download_mode: audio\n"
                "default_video_quality: 720p\n"
                "default_audio_quality: low\n"
                "retry_on_network_failure: 5\n"
                "default_exists_behavior: overwrite\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"HOME": str(home)}):
                loaded_config = config.load_config(config_path)

        self.assertEqual(loaded_config.output_dir, home / "Videos")
        self.assertEqual(loaded_config.ffmpeg_path, str(home / "bin" / "ffmpeg"))
        self.assertEqual(loaded_config.default_lang, "en")
        self.assertEqual(loaded_config.default_download_mode, config.DownloadMode.AUDIO)
        self.assertEqual(loaded_config.default_video_quality.label, "720p")
        self.assertEqual(loaded_config.default_audio_quality.label, "low")
        self.assertEqual(loaded_config.retry_on_network_failure, 5)
        self.assertEqual(
            loaded_config.default_exists_behavior,
            config.FileExistsBehavior.OVERWRITE,
        )

    def test_missing_optional_keys_use_defaults(self) -> None:
        loaded_config = config.config_from_mapping(
            {
                "output_dir": "/tmp/dbdvdl-output",
                "ffmpeg_path": "ffmpeg",
                "default_lang": "en",
            }
        )

        self.assertEqual(loaded_config.output_dir, Path("/tmp/dbdvdl-output"))
        self.assertEqual(loaded_config.ffmpeg_path, "ffmpeg")
        self.assertEqual(loaded_config.default_lang, "en")
        self.assertEqual(
            loaded_config.default_download_mode,
            config.DEFAULT_DOWNLOAD_MODE,
        )
        self.assertEqual(
            loaded_config.default_video_quality,
            config.DEFAULT_VIDEO_QUALITY,
        )
        self.assertEqual(
            loaded_config.default_audio_quality,
            config.DEFAULT_AUDIO_QUALITY,
        )
        self.assertEqual(
            loaded_config.retry_on_network_failure,
            config.DEFAULT_RETRY_ON_NETWORK_FAILURE,
        )
        self.assertEqual(
            loaded_config.default_exists_behavior,
            config.DEFAULT_EXISTS_BEHAVIOR,
        )

    def test_unknown_keys_are_ignored(self) -> None:
        loaded_config = config.config_from_mapping(
            {
                "output_dir": "/tmp/dbdvdl-output",
                "ffmpeg_path": "ffmpeg",
                "default_lang": "en",
                "default_download_mode": "audio",
                "default_video_quality": "1080p",
                "default_audio_quality": "medium",
                "retry_on_network_failure": 4,
                "default_exists_behavior": "fail",
                "future": "accepted",
            }
        )

        self.assertEqual(loaded_config.output_dir, Path("/tmp/dbdvdl-output"))
        self.assertEqual(loaded_config.ffmpeg_path, "ffmpeg")
        self.assertEqual(loaded_config.default_lang, "en")
        self.assertEqual(loaded_config.default_download_mode, config.DownloadMode.AUDIO)
        self.assertEqual(loaded_config.default_video_quality.label, "1080p")
        self.assertEqual(loaded_config.default_audio_quality.label, "medium")
        self.assertEqual(loaded_config.retry_on_network_failure, 4)
        self.assertEqual(
            loaded_config.default_exists_behavior,
            config.FileExistsBehavior.FAIL,
        )

    def test_missing_ffmpeg_path_fails(self) -> None:
        with self.assertRaises(config.ConfigError) as context:
            config.config_from_mapping(
                {
                    "output_dir": "/tmp/dbdvdl-output",
                    "default_lang": "en",
                }
            )

        self.assertIn("ffmpeg_path", str(context.exception))

    def test_missing_default_lang_fails(self) -> None:
        with self.assertRaises(config.ConfigError) as context:
            config.config_from_mapping(
                {
                    "output_dir": "/tmp/dbdvdl-output",
                    "ffmpeg_path": "ffmpeg",
                }
            )

        self.assertIn("default_lang", str(context.exception))

    def test_wrong_ffmpeg_path_type_fails(self) -> None:
        with self.assertRaises(config.ConfigError) as context:
            config.config_from_mapping(
                {
                    "output_dir": "/tmp/dbdvdl-output",
                    "ffmpeg_path": 123,
                    "default_lang": "en",
                }
            )

        self.assertIn("ffmpeg_path", str(context.exception))

    def test_wrong_default_lang_type_fails(self) -> None:
        with self.assertRaises(config.ConfigError) as context:
            config.config_from_mapping(
                {
                    "output_dir": "/tmp/dbdvdl-output",
                    "ffmpeg_path": "ffmpeg",
                    "default_lang": 123,
                }
            )

        self.assertIn("default_lang", str(context.exception))

    def test_empty_default_lang_fails(self) -> None:
        with self.assertRaises(config.ConfigError) as context:
            config.normalize_default_lang(" ")

        self.assertIn("default_lang", str(context.exception))

    def test_download_mode_accepts_video_and_audio(self) -> None:
        self.assertEqual(
            config.normalize_download_mode("video"),
            config.DownloadMode.VIDEO,
        )
        self.assertEqual(
            config.normalize_download_mode("audio"),
            config.DownloadMode.AUDIO,
        )

    def test_invalid_download_mode_fails(self) -> None:
        with self.assertRaises(config.ConfigError) as context:
            config.normalize_download_mode("mp3")

        self.assertIn("default_download_mode", str(context.exception))

    def test_wrong_download_mode_type_fails(self) -> None:
        with self.assertRaises(config.ConfigError) as context:
            config.normalize_download_mode(123)

        self.assertIn("default_download_mode", str(context.exception))

    def test_exists_behavior_accepts_supported_values(self) -> None:
        self.assertEqual(
            config.normalize_exists_behavior("skip"),
            config.FileExistsBehavior.SKIP,
        )
        self.assertEqual(
            config.normalize_exists_behavior(" fail "),
            config.FileExistsBehavior.FAIL,
        )
        self.assertEqual(
            config.normalize_exists_behavior("overwrite"),
            config.FileExistsBehavior.OVERWRITE,
        )

    def test_invalid_exists_behavior_fails(self) -> None:
        with self.assertRaises(config.ConfigError) as context:
            config.normalize_exists_behavior("replace")

        self.assertIn("default_exists_behavior", str(context.exception))

    def test_wrong_exists_behavior_type_fails(self) -> None:
        with self.assertRaises(config.ConfigError) as context:
            config.normalize_exists_behavior(True)

        self.assertIn("default_exists_behavior", str(context.exception))

    def test_video_quality_accepts_presets_and_exact_resolutions(self) -> None:
        self.assertEqual(config.normalize_video_quality("best").label, "best")
        self.assertEqual(config.normalize_video_quality(" medium ").label, "medium")
        self.assertEqual(config.normalize_video_quality("720P").label, "720p")

    def test_invalid_video_quality_fails(self) -> None:
        for value in ("1p", "0p", "-100p", "720", "720 p", "", "abc"):
            with self.subTest(value=value):
                with self.assertRaises(config.ConfigError) as context:
                    config.normalize_video_quality(value)

                self.assertIn("default_video_quality", str(context.exception))

    def test_wrong_video_quality_type_fails(self) -> None:
        for value in (None, True, ["720p"], {"quality": "720p"}):
            with self.subTest(value=value):
                with self.assertRaises(config.ConfigError) as context:
                    config.normalize_video_quality(value)

                self.assertIn("default_video_quality", str(context.exception))

    def test_audio_quality_accepts_presets(self) -> None:
        self.assertEqual(config.normalize_audio_quality("best").label, "best")
        self.assertEqual(config.normalize_audio_quality(" LOW ").label, "low")

    def test_invalid_audio_quality_fails(self) -> None:
        for value in ("128k", "720p", "", "abc"):
            with self.subTest(value=value):
                with self.assertRaises(config.ConfigError) as context:
                    config.normalize_audio_quality(value)

                self.assertIn("default_audio_quality", str(context.exception))

    def test_wrong_audio_quality_type_fails(self) -> None:
        for value in (None, False, ["best"], {"quality": "best"}):
            with self.subTest(value=value):
                with self.assertRaises(config.ConfigError) as context:
                    config.normalize_audio_quality(value)

                self.assertIn("default_audio_quality", str(context.exception))

    def test_zero_retry_on_network_failure_is_allowed(self) -> None:
        self.assertEqual(config.normalize_retry_on_network_failure(0), 0)

    def test_negative_retry_on_network_failure_fails(self) -> None:
        with self.assertRaises(config.ConfigError) as context:
            config.normalize_retry_on_network_failure(-1)

        self.assertIn("retry_on_network_failure", str(context.exception))

    def test_string_retry_on_network_failure_fails(self) -> None:
        with self.assertRaises(config.ConfigError) as context:
            config.normalize_retry_on_network_failure("3")

        self.assertIn("retry_on_network_failure", str(context.exception))

    def test_bool_retry_on_network_failure_fails(self) -> None:
        with self.assertRaises(config.ConfigError) as context:
            config.normalize_retry_on_network_failure(True)

        self.assertIn("retry_on_network_failure", str(context.exception))

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
