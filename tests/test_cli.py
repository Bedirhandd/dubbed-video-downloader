from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from dubbed_video_downloader import config
from dubbed_video_downloader import core
from dubbed_video_downloader import errors
from dubbed_video_downloader import quality
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
                "output_dir: ~/Downloads/dbdvdl-output\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n"
                "default_download_mode: video\n"
                "default_video_quality: best\n"
                "default_audio_quality: best\n"
                "retry_on_network_failure: 3\n"
                "default_exists_behavior: skip\n",
            )

    def test_init_refuses_overwrite_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            first = self.runner.invoke(app, ["init"], env={"HOME": tmpdir})
            second = self.runner.invoke(app, ["init"], env={"HOME": tmpdir})

        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(second.exit_code, 1, second.output)
        self.assertIn("--force", second.output)

    def test_config_init_writes_default_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(app, ["config", "init"], env={"HOME": tmpdir})
            config_path = (
                Path(tmpdir)
                / ".config"
                / "dubbed-video-downloader"
                / "config.yaml"
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertEqual(
                config_path.read_text(encoding="utf-8"),
                "output_dir: ~/Downloads/dbdvdl-output\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n"
                "default_download_mode: video\n"
                "default_video_quality: best\n"
                "default_audio_quality: best\n"
                "retry_on_network_failure: 3\n"
                "default_exists_behavior: skip\n",
            )

    def test_init_writes_custom_default_lang(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(
                app,
                ["init", "--default-lang", "tr"],
                env={"HOME": tmpdir},
            )
            config_path = (
                Path(tmpdir)
                / ".config"
                / "dubbed-video-downloader"
                / "config.yaml"
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn(
                "default_lang: tr\n",
                config_path.read_text(encoding="utf-8"),
            )

    def test_config_init_writes_custom_default_lang(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(
                app,
                ["config", "init", "--default-lang", "tr"],
                env={"HOME": tmpdir},
            )
            config_path = (
                Path(tmpdir)
                / ".config"
                / "dubbed-video-downloader"
                / "config.yaml"
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn(
                "default_lang: tr\n",
                config_path.read_text(encoding="utf-8"),
            )

    def test_init_writes_custom_default_download_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(
                app,
                ["init", "--default-download-mode", "audio"],
                env={"HOME": tmpdir},
            )
            config_path = (
                Path(tmpdir)
                / ".config"
                / "dubbed-video-downloader"
                / "config.yaml"
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn(
                "default_download_mode: audio\n",
                config_path.read_text(encoding="utf-8"),
            )

    def test_config_init_writes_custom_default_download_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(
                app,
                ["config", "init", "--default-download-mode", "audio"],
                env={"HOME": tmpdir},
            )
            config_path = (
                Path(tmpdir)
                / ".config"
                / "dubbed-video-downloader"
                / "config.yaml"
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn(
                "default_download_mode: audio\n",
                config_path.read_text(encoding="utf-8"),
            )

    def test_init_writes_custom_default_qualities(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(
                app,
                [
                    "init",
                    "--default-video-quality",
                    "720p",
                    "--default-audio-quality",
                    "low",
                ],
                env={"HOME": tmpdir},
            )
            config_path = (
                Path(tmpdir)
                / ".config"
                / "dubbed-video-downloader"
                / "config.yaml"
            )

            self.assertEqual(result.exit_code, 0, result.output)
            written_config = config_path.read_text(encoding="utf-8")
            self.assertIn("default_video_quality: 720p\n", written_config)
            self.assertIn("default_audio_quality: low\n", written_config)

    def test_init_writes_custom_retry_on_network_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(
                app,
                ["init", "--retry-on-network-failure", "5"],
                env={"HOME": tmpdir},
            )
            config_path = (
                Path(tmpdir)
                / ".config"
                / "dubbed-video-downloader"
                / "config.yaml"
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn(
                "retry_on_network_failure: 5\n",
                config_path.read_text(encoding="utf-8"),
            )

    def test_init_writes_custom_default_exists_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(
                app,
                ["init", "--default-exists-behavior", "overwrite"],
                env={"HOME": tmpdir},
            )
            config_path = (
                Path(tmpdir)
                / ".config"
                / "dubbed-video-downloader"
                / "config.yaml"
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn(
                "default_exists_behavior: overwrite\n",
                config_path.read_text(encoding="utf-8"),
            )

    def test_config_init_writes_custom_default_exists_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(
                app,
                ["config", "init", "--default-exists-behavior", "fail"],
                env={"HOME": tmpdir},
            )
            config_path = (
                Path(tmpdir)
                / ".config"
                / "dubbed-video-downloader"
                / "config.yaml"
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn(
                "default_exists_behavior: fail\n",
                config_path.read_text(encoding="utf-8"),
            )

    def test_config_show_displays_resolved_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n",
                encoding="utf-8",
            )

            result = self.runner.invoke(
                app,
                ["config", "show"],
                env={"HOME": tmpdir},
            )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn(f"Config path: {config_path}", result.output)
        self.assertIn(
            f"Output directory: {home / 'Downloads' / 'from-config'}",
            result.output,
        )
        self.assertIn("FFmpeg path: ffmpeg", result.output)
        self.assertIn("Default language: en", result.output)
        self.assertIn("Default download mode: video", result.output)
        self.assertIn("Default video quality: best", result.output)
        self.assertIn("Default audio quality: best", result.output)
        self.assertIn("Retry on network failure: 3", result.output)
        self.assertIn("Default exists behavior: skip", result.output)

    def test_config_show_requires_existing_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(
                app,
                ["config", "show"],
                env={"HOME": tmpdir},
            )

        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("dbdvdl init", result.output)

    def test_config_remove_yes_removes_config_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_dir = home / ".config" / "dubbed-video-downloader"
            config_dir.mkdir(parents=True)
            (config_dir / "config.yaml").write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n",
                encoding="utf-8",
            )

            result = self.runner.invoke(
                app,
                ["config", "remove", "--yes"],
                env={"HOME": tmpdir},
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertFalse(config_dir.exists())
            self.assertIn(f"Removed config directory: {config_dir}", result.output)
            self.assertIn("dbdvdl init", result.output)

    def test_config_remove_yes_succeeds_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(
                app,
                ["config", "remove", "--yes"],
                env={"HOME": tmpdir},
            )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Nothing to remove.", result.output)

    def test_config_remove_cancels_when_user_answers_no(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_dir = home / ".config" / "dubbed-video-downloader"
            config_dir.mkdir(parents=True)
            (config_dir / "config.yaml").write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n",
                encoding="utf-8",
            )

            with patch(
                "dubbed_video_downloader.cli._stdin_is_interactive",
                return_value=True,
            ):
                result = self.runner.invoke(
                    app,
                    ["config", "remove"],
                    input="n\n",
                    env={"HOME": tmpdir},
                )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertTrue(config_dir.exists())
            self.assertIn("Config removal cancelled.", result.output)

    def test_config_remove_refuses_non_interactive_without_yes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_dir = home / ".config" / "dubbed-video-downloader"
            config_dir.mkdir(parents=True)
            (config_dir / "config.yaml").write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n",
                encoding="utf-8",
            )

            with patch(
                "dubbed_video_downloader.cli._stdin_is_interactive",
                return_value=False,
            ):
                result = self.runner.invoke(
                    app,
                    ["config", "remove"],
                    env={"HOME": tmpdir},
                )

            self.assertEqual(result.exit_code, 1, result.output)
            self.assertTrue(config_dir.exists())
            self.assertIn("--yes", result.output)

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

    def test_download_help_includes_dry_run_and_verbose(self) -> None:
        result = self.runner.invoke(app, ["download", "--help"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("--dry-run", result.output)
        self.assertIn("--verbose", result.output)
        self.assertIn("--debug", result.output)
        self.assertIn("--mode", result.output)
        self.assertIn("--video-quality", result.output)
        self.assertIn("--audio-quality", result.output)
        self.assertIn("--retry-on-network", result.output)
        self.assertIn("--if-exists", result.output)
        self.assertIn("Overrides config", result.output)
        self.assertIn("default.", result.output)
        self.assertNotIn("[default: tr]", result.output)

    def test_download_uses_config_and_allows_cli_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: tr\n"
                "default_download_mode: audio\n"
                "default_video_quality: low\n"
                "default_audio_quality: medium\n"
                "retry_on_network_failure: 4\n"
                "default_exists_behavior: fail\n",
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
                        "--mode",
                        "video",
                        "--video-quality",
                        "720p",
                        "--audio-quality",
                        "low",
                        "--output-dir",
                        str(override_output),
                        "--ffmpeg-path",
                        str(override_ffmpeg),
                        "--retry-on-network-failure",
                        "6",
                        "--if-exists",
                        "overwrite",
                    ],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 0, result.output)
        download.assert_called_once_with(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="en",
            download_mode=core.DownloadMode.VIDEO,
            ffmpeg_path=str(override_ffmpeg),
            output_dir=override_output,
            video_quality=quality.VideoQuality(
                quality.VideoQualityKind.EXACT,
                720,
            ),
            audio_quality=quality.AudioQuality(quality.AudioQualityKind.LOW),
            verbose=False,
            debug=False,
            retry_on_network_failure=6,
            exists_behavior=config.FileExistsBehavior.OVERWRITE,
        )

    def test_download_verbose_passes_through_to_core_download(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n"
                "default_download_mode: audio\n",
                encoding="utf-8",
            )

            with patch("dubbed_video_downloader.cli.core.download") as download:
                result = self.runner.invoke(
                    app,
                    [
                        "download",
                        "https://www.youtube.com/watch?v=EXAMPLE",
                        "--verbose",
                    ],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 0, result.output)
        download.assert_called_once_with(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="en",
            download_mode=core.DownloadMode.AUDIO,
            ffmpeg_path=None,
            output_dir=home / "Downloads" / "from-config",
            video_quality=config.DEFAULT_VIDEO_QUALITY,
            audio_quality=config.DEFAULT_AUDIO_QUALITY,
            verbose=True,
            debug=False,
            retry_on_network_failure=3,
            exists_behavior=config.DEFAULT_EXISTS_BEHAVIOR,
        )

    def test_download_debug_passes_through_to_core_download(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n",
                encoding="utf-8",
            )

            with patch("dubbed_video_downloader.cli.core.download") as download:
                result = self.runner.invoke(
                    app,
                    [
                        "download",
                        "https://www.youtube.com/watch?v=EXAMPLE",
                        "--debug",
                    ],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 0, result.output)
        download.assert_called_once_with(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="en",
            download_mode=core.DownloadMode.VIDEO,
            ffmpeg_path=None,
            output_dir=home / "Downloads" / "from-config",
            video_quality=config.DEFAULT_VIDEO_QUALITY,
            audio_quality=config.DEFAULT_AUDIO_QUALITY,
            verbose=False,
            debug=True,
            retry_on_network_failure=3,
            exists_behavior=config.DEFAULT_EXISTS_BEHAVIOR,
        )

    def test_download_uses_config_default_exists_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n"
                "default_exists_behavior: fail\n",
                encoding="utf-8",
            )

            with patch("dubbed_video_downloader.cli.core.download") as download:
                result = self.runner.invoke(
                    app,
                    ["download", "https://www.youtube.com/watch?v=EXAMPLE"],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(
            download.call_args.kwargs["exists_behavior"],
            config.FileExistsBehavior.FAIL,
        )

    def test_download_reports_skipped_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n",
                encoding="utf-8",
            )
            output_path = home / "Downloads" / "from-config" / "en" / "Title.mkv"

            with patch(
                "dubbed_video_downloader.cli.core.download",
                return_value=core.DownloadResult(
                    status=core.DownloadStatus.SKIPPED,
                    output_path=output_path,
                ),
            ) as download:
                result = self.runner.invoke(
                    app,
                    ["download", "https://www.youtube.com/watch?v=EXAMPLE"],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Skipped", result.output)
        self.assertIn(f"Output already exists: {output_path}", result.output)
        download.assert_called_once()

    def test_download_rejects_invalid_if_exists_before_network_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n",
                encoding="utf-8",
            )

            with patch("dubbed_video_downloader.cli.core.download") as download:
                result = self.runner.invoke(
                    app,
                    [
                        "download",
                        "https://www.youtube.com/watch?v=EXAMPLE",
                        "--if-exists",
                        "replace",
                    ],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 2, result.output)
        self.assertIn("--if-exists", result.output)
        download.assert_not_called()

    def test_download_dry_run_requires_config_before_network_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("dubbed_video_downloader.cli.core.plan_download") as plan:
                result = self.runner.invoke(
                    app,
                    [
                        "download",
                        "https://www.youtube.com/watch?v=EXAMPLE",
                        "--dry-run",
                    ],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("dbdvdl init", result.output)
        plan.assert_not_called()

    def test_download_rejects_negative_retry_before_network_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n",
                encoding="utf-8",
            )

            with patch("dubbed_video_downloader.cli.core.download") as download:
                result = self.runner.invoke(
                    app,
                    [
                        "download",
                        "https://www.youtube.com/watch?v=EXAMPLE",
                        "--retry-on-network-failure",
                        "-1",
                    ],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("retry_on_network_failure", result.output)
        download.assert_not_called()

    def test_download_rejects_invalid_mode_before_network_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n",
                encoding="utf-8",
            )

            with patch("dubbed_video_downloader.cli.core.download") as download:
                result = self.runner.invoke(
                    app,
                    [
                        "download",
                        "https://www.youtube.com/watch?v=EXAMPLE",
                        "--mode",
                        "mp3",
                    ],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 2, result.output)
        self.assertIn("--mode", result.output)
        self.assertIn("mp3", result.output)
        download.assert_not_called()

    def test_download_rejects_video_quality_in_audio_mode_before_network_work(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n"
                "default_download_mode: audio\n",
                encoding="utf-8",
            )

            with patch("dubbed_video_downloader.cli.core.download") as download:
                result = self.runner.invoke(
                    app,
                    [
                        "download",
                        "https://www.youtube.com/watch?v=EXAMPLE",
                        "--video-quality",
                        "720p",
                    ],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("--video-quality", result.output)
        download.assert_not_called()

    def test_download_rejects_invalid_audio_quality_before_network_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n",
                encoding="utf-8",
            )

            with patch("dubbed_video_downloader.cli.core.download") as download:
                result = self.runner.invoke(
                    app,
                    [
                        "download",
                        "https://www.youtube.com/watch?v=EXAMPLE",
                        "--audio-quality",
                        "128k",
                    ],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("audio_quality", result.output)
        download.assert_not_called()

    def test_download_rejects_invalid_video_quality_before_network_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n",
                encoding="utf-8",
            )

            with patch("dubbed_video_downloader.cli.core.download") as download:
                result = self.runner.invoke(
                    app,
                    [
                        "download",
                        "https://www.youtube.com/watch?v=EXAMPLE",
                        "--video-quality",
                        "-100p",
                    ],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("video_quality", result.output)
        download.assert_not_called()

    def test_download_dry_run_uses_config_and_allows_cli_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: tr\n"
                "default_download_mode: video\n"
                "retry_on_network_failure: 4\n",
                encoding="utf-8",
            )
            override_output = home / "Videos" / "override"
            override_ffmpeg = home / "bin" / "ffmpeg"
            planned_output = override_output / "en" / "Channel" / "Title" / "Title.mkv"

            with (
                patch("dubbed_video_downloader.cli.core.download") as download,
                patch(
                    "dubbed_video_downloader.cli.core.plan_download",
                    return_value=core.DownloadPlan(
                        url="https://www.youtube.com/watch?v=EXAMPLE",
                        lang="en",
                        download_mode=core.DownloadMode.AUDIO,
                        title="Title",
                        uploader="Channel",
                        available_langs=("en", "tr"),
                        output_path=planned_output,
                    ),
                ) as plan,
            ):
                result = self.runner.invoke(
                    app,
                    [
                        "download",
                        "https://www.youtube.com/watch?v=EXAMPLE",
                        "--lang",
                        "en",
                        "--mode",
                        "audio",
                        "--output-dir",
                        str(override_output),
                        "--ffmpeg-path",
                        str(override_ffmpeg),
                        "--dry-run",
                        "--retry-on-network-failure",
                        "6",
                    ],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 0, result.output)
        plan.assert_called_once_with(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="en",
            download_mode=core.DownloadMode.AUDIO,
            ffmpeg_path=str(override_ffmpeg),
            output_dir=override_output,
            video_quality=config.DEFAULT_VIDEO_QUALITY,
            audio_quality=config.DEFAULT_AUDIO_QUALITY,
            verbose=False,
            debug=False,
            retry_on_network_failure=6,
            exists_behavior=config.DEFAULT_EXISTS_BEHAVIOR,
        )
        download.assert_not_called()
        self.assertIn("Dry run: no files will be downloaded or created.", result.output)
        self.assertIn("Mode: audio", result.output)
        self.assertIn(f"Output: {planned_output}", result.output)

    def test_download_dry_run_uses_color_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n",
                encoding="utf-8",
            )

            with patch(
                "dubbed_video_downloader.cli.core.plan_download",
                return_value=core.DownloadPlan(
                    url="https://www.youtube.com/watch?v=EXAMPLE",
                    lang="en",
                    download_mode=core.DownloadMode.VIDEO,
                    title="Title",
                    uploader="Channel",
                    available_langs=("en",),
                    output_path=home / "Downloads" / "from-config" / "en" / "Title.mkv",
                ),
            ):
                result = self.runner.invoke(
                    app,
                    [
                        "download",
                        "https://www.youtube.com/watch?v=EXAMPLE",
                        "--dry-run",
                    ],
                    env={"HOME": tmpdir},
                    color=True,
                )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("\x1b[", result.output)
        self.assertIn("Title: ", result.output)
        self.assertIn("Channel: ", result.output)
        self.assertIn("Title\n", result.output)

    def test_download_dry_run_fails_when_existing_output_policy_is_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n"
                "default_exists_behavior: fail\n",
                encoding="utf-8",
            )
            output_path = home / "Downloads" / "from-config" / "en" / "Title.mkv"

            with patch(
                "dubbed_video_downloader.cli.core.plan_download",
                return_value=core.DownloadPlan(
                    url="https://www.youtube.com/watch?v=EXAMPLE",
                    lang="en",
                    title="Title",
                    uploader="Channel",
                    available_langs=("en",),
                    output_path=output_path,
                    exists_behavior=config.FileExistsBehavior.FAIL,
                    output_exists=True,
                ),
            ):
                result = self.runner.invoke(
                    app,
                    [
                        "download",
                        "https://www.youtube.com/watch?v=EXAMPLE",
                        "--dry-run",
                    ],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn(f"Output: {output_path}", result.output)
        self.assertIn("If output exists: fail", result.output)
        self.assertIn("Output exists: yes", result.output)
        self.assertIn("Error: Output already exists", result.output)

    def test_download_dry_run_verbose_passes_through_to_core_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n",
                encoding="utf-8",
            )

            with patch(
                "dubbed_video_downloader.cli.core.plan_download",
                return_value=core.DownloadPlan(
                    url="https://www.youtube.com/watch?v=EXAMPLE",
                    lang="en",
                    download_mode=core.DownloadMode.VIDEO,
                    title="Title",
                    uploader="Channel",
                    available_langs=("en",),
                    output_path=home / "Downloads" / "from-config" / "en" / "Title.mkv",
                ),
            ) as plan:
                result = self.runner.invoke(
                    app,
                    [
                        "download",
                        "https://www.youtube.com/watch?v=EXAMPLE",
                        "--dry-run",
                        "--verbose",
                    ],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 0, result.output)
        plan.assert_called_once_with(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="en",
            download_mode=core.DownloadMode.VIDEO,
            ffmpeg_path=None,
            output_dir=home / "Downloads" / "from-config",
            video_quality=config.DEFAULT_VIDEO_QUALITY,
            audio_quality=config.DEFAULT_AUDIO_QUALITY,
            verbose=True,
            debug=False,
            retry_on_network_failure=3,
            exists_behavior=config.DEFAULT_EXISTS_BEHAVIOR,
        )

    def test_download_dry_run_reports_plan_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n",
                encoding="utf-8",
            )

            with (
                patch("dubbed_video_downloader.cli.core.download") as download,
                patch(
                    "dubbed_video_downloader.cli.core.plan_download",
                    side_effect=errors.DownloadError("missing language"),
                ) as plan,
            ):
                result = self.runner.invoke(
                    app,
                    [
                        "download",
                        "https://www.youtube.com/watch?v=EXAMPLE",
                        "--dry-run",
                    ],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 1, result.output)
        plan.assert_called_once()
        download.assert_not_called()
        self.assertIn("Error: missing language", result.output)
        self.assertNotIn("Traceback", result.output)

    def test_download_dry_run_reports_traceback_with_debug(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n",
                encoding="utf-8",
            )

            with (
                patch("dubbed_video_downloader.cli.core.download") as download,
                patch(
                    "dubbed_video_downloader.cli.core.plan_download",
                    side_effect=errors.DownloadError("missing language"),
                ) as plan,
            ):
                result = self.runner.invoke(
                    app,
                    [
                        "download",
                        "https://www.youtube.com/watch?v=EXAMPLE",
                        "--dry-run",
                        "--debug",
                    ],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 1, result.output)
        plan.assert_called_once()
        download.assert_not_called()
        self.assertIn("Error: missing language", result.output)
        self.assertIn("Traceback", result.output)

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

    def test_langs_help_includes_verbose(self) -> None:
        result = self.runner.invoke(app, ["langs", "--help"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("--verbose", result.output)
        self.assertIn("--debug", result.output)
        self.assertIn("--retry-on-network", result.output)

    def test_langs_passes_verbose_false_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n",
                encoding="utf-8",
            )

            with patch(
                "dubbed_video_downloader.cli.core.get_available_audio_langs_for_url",
                return_value={"tr", "en"},
            ) as langs:
                result = self.runner.invoke(
                    app,
                    ["langs", "https://www.youtube.com/watch?v=EXAMPLE"],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 0, result.output)
        langs.assert_called_once_with(
            "https://www.youtube.com/watch?v=EXAMPLE",
            verbose=False,
            debug=False,
            retry_on_network_failure=3,
        )
        self.assertIn("en", result.output)
        self.assertIn("tr", result.output)

    def test_langs_passes_verbose_true(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n"
                "retry_on_network_failure: 4\n",
                encoding="utf-8",
            )

            with patch(
                "dubbed_video_downloader.cli.core.get_available_audio_langs_for_url",
                return_value={"tr"},
            ) as langs:
                result = self.runner.invoke(
                    app,
                    [
                        "langs",
                        "https://www.youtube.com/watch?v=EXAMPLE",
                        "--verbose",
                        "--retry-on-network-failure",
                        "6",
                    ],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 0, result.output)
        langs.assert_called_once_with(
            "https://www.youtube.com/watch?v=EXAMPLE",
            verbose=True,
            debug=False,
            retry_on_network_failure=6,
        )

    def test_langs_passes_debug_true(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n",
                encoding="utf-8",
            )

            with patch(
                "dubbed_video_downloader.cli.core.get_available_audio_langs_for_url",
                return_value={"tr"},
            ) as langs:
                result = self.runner.invoke(
                    app,
                    [
                        "langs",
                        "https://www.youtube.com/watch?v=EXAMPLE",
                        "--debug",
                    ],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 0, result.output)
        langs.assert_called_once_with(
            "https://www.youtube.com/watch?v=EXAMPLE",
            verbose=False,
            debug=True,
            retry_on_network_failure=3,
        )

    def test_langs_reports_metadata_error_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n",
                encoding="utf-8",
            )

            with patch(
                "dubbed_video_downloader.cli.core.get_available_audio_langs_for_url",
                side_effect=errors.MetadataExtractionError("metadata failed"),
            ) as langs:
                result = self.runner.invoke(
                    app,
                    ["langs", "https://www.youtube.com/watch?v=EXAMPLE"],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 1, result.output)
        langs.assert_called_once()
        self.assertIn("Error: metadata failed", result.output)
        self.assertNotIn("Traceback", result.output)

    def test_langs_reports_metadata_error_traceback_with_debug(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n",
                encoding="utf-8",
            )

            with patch(
                "dubbed_video_downloader.cli.core.get_available_audio_langs_for_url",
                side_effect=errors.MetadataExtractionError("metadata failed"),
            ) as langs:
                result = self.runner.invoke(
                    app,
                    [
                        "langs",
                        "https://www.youtube.com/watch?v=EXAMPLE",
                        "--debug",
                    ],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 1, result.output)
        langs.assert_called_once()
        self.assertIn("Error: metadata failed", result.output)
        self.assertIn("Traceback", result.output)

    def test_qualities_requires_config_before_network_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("dubbed_video_downloader.cli.core.get_quality_report") as report:
                result = self.runner.invoke(
                    app,
                    ["qualities", "https://www.youtube.com/watch?v=EXAMPLE"],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("dbdvdl init", result.output)
        report.assert_not_called()

    def test_qualities_reports_domain_error_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n",
                encoding="utf-8",
            )

            with patch(
                "dubbed_video_downloader.cli.core.get_quality_report",
                side_effect=errors.LanguageNotFoundError("missing language"),
            ) as report:
                result = self.runner.invoke(
                    app,
                    ["qualities", "https://www.youtube.com/watch?v=EXAMPLE"],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 1, result.output)
        report.assert_called_once()
        self.assertIn("Error: missing language", result.output)
        self.assertNotIn("Traceback", result.output)

    def test_qualities_reports_domain_error_traceback_with_debug(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n",
                encoding="utf-8",
            )

            with patch(
                "dubbed_video_downloader.cli.core.get_quality_report",
                side_effect=errors.LanguageNotFoundError("missing language"),
            ) as report:
                result = self.runner.invoke(
                    app,
                    [
                        "qualities",
                        "https://www.youtube.com/watch?v=EXAMPLE",
                        "--debug",
                    ],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 1, result.output)
        report.assert_called_once()
        self.assertIn("Error: missing language", result.output)
        self.assertIn("Traceback", result.output)

    def test_qualities_uses_config_and_allows_lang_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n"
                "retry_on_network_failure: 4\n",
                encoding="utf-8",
            )

            with patch(
                "dubbed_video_downloader.cli.core.get_quality_report",
                return_value=core.QualityReport(
                    url="https://www.youtube.com/watch?v=EXAMPLE",
                    lang="tr",
                    title="Title",
                    uploader="Channel",
                    available_langs=("en", "tr"),
                    video_qualities=("360p", "720p"),
                    audio_qualities=("50k", "160k"),
                ),
            ) as report:
                result = self.runner.invoke(
                    app,
                    [
                        "qualities",
                        "https://www.youtube.com/watch?v=EXAMPLE",
                        "--lang",
                        "tr",
                        "--retry-on-network-failure",
                        "6",
                    ],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 0, result.output)
        report.assert_called_once_with(
            "https://www.youtube.com/watch?v=EXAMPLE",
            "tr",
            verbose=False,
            debug=False,
            retry_on_network_failure=6,
        )
        self.assertIn("Video qualities: 360p, 720p", result.output)
        self.assertIn("Audio qualities: 50k, 160k", result.output)


if __name__ == "__main__":
    unittest.main()
