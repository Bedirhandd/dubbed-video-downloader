from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from dubbed_video_downloader import core
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
                "output_dir: ~/Downloads/dbdvdl-output\nffmpeg_path: ffmpeg\n",
            )

    def test_config_show_displays_resolved_values(self) -> None:
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
                "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\n",
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
                "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\n",
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
                "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\n",
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
            verbose=False,
        )

    def test_download_verbose_passes_through_to_core_download(self) -> None:
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
            lang="tr",
            ffmpeg_path=None,
            output_dir=home / "Downloads" / "from-config",
            verbose=True,
        )

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

    def test_download_dry_run_uses_config_and_allows_cli_overrides(self) -> None:
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
            planned_output = override_output / "en" / "Channel" / "Title" / "Title.mkv"

            with (
                patch("dubbed_video_downloader.cli.core.download") as download,
                patch(
                    "dubbed_video_downloader.cli.core.plan_download",
                    return_value=core.DownloadPlan(
                        url="https://www.youtube.com/watch?v=EXAMPLE",
                        lang="en",
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
                        "--output-dir",
                        str(override_output),
                        "--ffmpeg-path",
                        str(override_ffmpeg),
                        "--dry-run",
                    ],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 0, result.output)
        plan.assert_called_once_with(
            url="https://www.youtube.com/watch?v=EXAMPLE",
            lang="en",
            ffmpeg_path=str(override_ffmpeg),
            output_dir=override_output,
            verbose=False,
        )
        download.assert_not_called()
        self.assertIn("Dry run: no files will be downloaded or created.", result.output)
        self.assertIn(f"Output: {planned_output}", result.output)

    def test_download_dry_run_uses_color_when_enabled(self) -> None:
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

            with patch(
                "dubbed_video_downloader.cli.core.plan_download",
                return_value=core.DownloadPlan(
                    url="https://www.youtube.com/watch?v=EXAMPLE",
                    lang="tr",
                    title="Title",
                    uploader="Channel",
                    available_langs=("tr",),
                    output_path=home / "Downloads" / "from-config" / "tr" / "Title.mkv",
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

    def test_download_dry_run_verbose_passes_through_to_core_plan(self) -> None:
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

            with patch(
                "dubbed_video_downloader.cli.core.plan_download",
                return_value=core.DownloadPlan(
                    url="https://www.youtube.com/watch?v=EXAMPLE",
                    lang="tr",
                    title="Title",
                    uploader="Channel",
                    available_langs=("tr",),
                    output_path=home / "Downloads" / "from-config" / "tr" / "Title.mkv",
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
            lang="tr",
            ffmpeg_path=None,
            output_dir=home / "Downloads" / "from-config",
            verbose=True,
        )

    def test_download_dry_run_reports_plan_failures(self) -> None:
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

            with (
                patch("dubbed_video_downloader.cli.core.download") as download,
                patch(
                    "dubbed_video_downloader.cli.core.plan_download",
                    side_effect=RuntimeError("missing language"),
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

    def test_langs_passes_verbose_false_by_default(self) -> None:
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
                "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\n",
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
                    ],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 0, result.output)
        langs.assert_called_once_with(
            "https://www.youtube.com/watch?v=EXAMPLE",
            verbose=True,
        )


if __name__ == "__main__":
    unittest.main()
