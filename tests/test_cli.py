from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import ANY, patch

from typer.testing import CliRunner

from dubbed_video_downloader import cli
from dubbed_video_downloader import config
from dubbed_video_downloader import core
from dubbed_video_downloader import errors
from dubbed_video_downloader import languages
from dubbed_video_downloader import quality
from dubbed_video_downloader.cli import app


def _plain_cli_output(text: str) -> str:
    without_ansi = re.sub(r"\x1b\[[0-9;]*m", "", text)
    return without_ansi.replace("\n", " ")


def _audio_inventory(
    *langs: str,
    skipped_invalid_count: int = 0,
    skipped_invalid_tags: tuple[str, ...] = (),
) -> languages.AudioLanguageInventory:
    return languages.AudioLanguageInventory(
        langs=frozenset(langs),
        skipped_invalid_count=skipped_invalid_count,
        skipped_invalid_tags=skipped_invalid_tags,
    )


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    @staticmethod
    def _download_result_with_file(
        output_path: Path,
        *,
        size_bytes: int = 0,
    ) -> core.DownloadResult:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if size_bytes:
            output_path.write_bytes(b"x" * size_bytes)
        else:
            output_path.touch()
        return core.DownloadResult(output_path=output_path)

    @staticmethod
    def _expected_config_yaml(**overrides: str) -> str:
        values = {
            "output_dir": "~/Downloads/dbdvdl-output",
            "ffmpeg_path": "ffmpeg",
            "default_lang": "en",
            "default_download_mode": "video",
            "default_video_quality": "best",
            "default_audio_quality": "best",
            "retry_on_network_failure": "3",
            "default_exists_behavior": "skip",
            "ask_for_disk_usage": "false",
        }
        values.update(overrides)
        return (
            f"output_dir: {values['output_dir']}\n"
            f"ffmpeg_path: {values['ffmpeg_path']}\n"
            f"default_lang: {values['default_lang']}\n"
            f"default_download_mode: {values['default_download_mode']}\n"
            f"default_video_quality: {values['default_video_quality']}\n"
            f"default_audio_quality: {values['default_audio_quality']}\n"
            f"retry_on_network_failure: {values['retry_on_network_failure']}\n"
            f"default_exists_behavior: {values['default_exists_behavior']}\n"
            f"ask_for_disk_usage: {values['ask_for_disk_usage']}\n"
        )

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
                self._expected_config_yaml(),
            )

    def test_init_default_writes_config_without_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "dubbed_video_downloader.cli._stdin_is_interactive",
                return_value=True,
            ):
                with patch(
                    "dubbed_video_downloader.cli.shutil.which",
                    return_value=None,
                ):
                    result = self.runner.invoke(
                        app,
                        ["init", "--default"],
                        env={"HOME": tmpdir},
                    )
            config_path = (
                Path(tmpdir)
                / ".config"
                / "dubbed-video-downloader"
                / "config.yaml"
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertEqual(
                config_path.read_text(encoding="utf-8"),
                self._expected_config_yaml(),
            )
            self.assertNotIn("(press Enter to use)", result.output)
            self.assertNotIn(
                "Downloads will be saved under this directory.",
                result.output,
            )

    def test_init_default_allows_partial_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "dubbed_video_downloader.cli.shutil.which",
                return_value=None,
            ):
                result = self.runner.invoke(
                    app,
                    ["init", "--default", "--default-lang", "tr"],
                    env={"HOME": tmpdir},
                )
            config_path = (
                Path(tmpdir)
                / ".config"
                / "dubbed-video-downloader"
                / "config.yaml"
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertEqual(
                config_path.read_text(encoding="utf-8"),
                self._expected_config_yaml(default_lang="tr"),
            )

    def test_init_default_autodetects_ffmpeg(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "dubbed_video_downloader.cli.shutil.which",
                return_value="/usr/bin/ffmpeg",
            ):
                result = self.runner.invoke(
                    app,
                    ["init", "--default"],
                    env={"HOME": tmpdir},
                )
            config_path = (
                Path(tmpdir)
                / ".config"
                / "dubbed-video-downloader"
                / "config.yaml"
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertEqual(
                config_path.read_text(encoding="utf-8"),
                self._expected_config_yaml(ffmpeg_path="/usr/bin/ffmpeg"),
            )

    def test_init_default_ffmpeg_fallback_when_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "dubbed_video_downloader.cli.shutil.which",
                return_value=None,
            ):
                result = self.runner.invoke(
                    app,
                    ["init", "--default"],
                    env={"HOME": tmpdir},
                )
            config_path = (
                Path(tmpdir)
                / ".config"
                / "dubbed-video-downloader"
                / "config.yaml"
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertEqual(
                config_path.read_text(encoding="utf-8"),
                self._expected_config_yaml(),
            )

    def test_config_init_default_writes_config_without_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "dubbed_video_downloader.cli._stdin_is_interactive",
                return_value=True,
            ):
                with patch(
                    "dubbed_video_downloader.cli.shutil.which",
                    return_value=None,
                ):
                    result = self.runner.invoke(
                        app,
                        ["config", "init", "--default"],
                        env={"HOME": tmpdir},
                    )
            config_path = (
                Path(tmpdir)
                / ".config"
                / "dubbed-video-downloader"
                / "config.yaml"
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertEqual(
                config_path.read_text(encoding="utf-8"),
                self._expected_config_yaml(),
            )
            self.assertNotIn("(press Enter to use)", result.output)

    def test_init_default_still_requires_force_to_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            first = self.runner.invoke(
                app,
                ["init", "--default"],
                env={"HOME": tmpdir},
            )
            with patch(
                "dubbed_video_downloader.cli._stdin_is_interactive",
                return_value=True,
            ):
                second = self.runner.invoke(
                    app,
                    ["init", "--default"],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(second.exit_code, 1, second.output)
        self.assertIn("--force", second.output)
        self.assertNotIn("Output directory", second.output)
        self.assertNotIn("(press Enter to use)", second.output)

    def test_init_default_explicit_ffmpeg_path_skips_autodetect(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "dubbed_video_downloader.cli._stdin_is_interactive",
                return_value=True,
            ):
                with patch(
                    "dubbed_video_downloader.cli.shutil.which",
                    return_value="/usr/bin/ffmpeg",
                ):
                    result = self.runner.invoke(
                        app,
                        [
                            "init",
                            "--default",
                            "--ffmpeg-path",
                            "/opt/ffmpeg/bin/ffmpeg",
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
            self.assertEqual(
                config_path.read_text(encoding="utf-8"),
                self._expected_config_yaml(ffmpeg_path="/opt/ffmpeg/bin/ffmpeg"),
            )
            self.assertNotIn("(press Enter to use)", result.output)

    def test_init_default_explicit_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "dubbed_video_downloader.cli.shutil.which",
                return_value=None,
            ):
                result = self.runner.invoke(
                    app,
                    [
                        "init",
                        "--default",
                        "--output-dir",
                        "~/Videos/custom",
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
            self.assertEqual(
                config_path.read_text(encoding="utf-8"),
                self._expected_config_yaml(output_dir="~/Videos/custom"),
            )

    def test_init_default_multiple_explicit_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "dubbed_video_downloader.cli._stdin_is_interactive",
                return_value=True,
            ):
                with patch(
                    "dubbed_video_downloader.cli.shutil.which",
                    return_value=None,
                ):
                    result = self.runner.invoke(
                        app,
                        [
                            "init",
                            "--default",
                            "--default-lang",
                            "tr",
                            "--default-download-mode",
                            "audio",
                            "--default-video-quality",
                            "720p",
                            "--default-audio-quality",
                            "low",
                            "--retry-on-network-failure",
                            "0",
                            "--default-exists-behavior",
                            "fail",
                            "--no-ask-for-disk-usage",
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
            self.assertEqual(
                config_path.read_text(encoding="utf-8"),
                self._expected_config_yaml(
                    default_lang="tr",
                    default_download_mode="audio",
                    default_video_quality="720p",
                    default_audio_quality="low",
                    retry_on_network_failure="0",
                    default_exists_behavior="fail",
                    ask_for_disk_usage="false",
                ),
            )
            self.assertNotIn("(press Enter to use)", result.output)

    def test_init_default_with_force_overwrites_existing_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            first = self.runner.invoke(
                app,
                ["init", "--default"],
                env={"HOME": tmpdir},
            )
            with patch(
                "dubbed_video_downloader.cli._stdin_is_interactive",
                return_value=True,
            ):
                with patch(
                    "dubbed_video_downloader.cli.shutil.which",
                    return_value=None,
                ):
                    second = self.runner.invoke(
                        app,
                        ["init", "--default", "--force", "--default-lang", "tr"],
                        env={"HOME": tmpdir},
                    )
            config_path = (
                Path(tmpdir)
                / ".config"
                / "dubbed-video-downloader"
                / "config.yaml"
            )

            self.assertEqual(first.exit_code, 0, first.output)
            self.assertEqual(second.exit_code, 0, second.output)
            self.assertEqual(
                config_path.read_text(encoding="utf-8"),
                self._expected_config_yaml(default_lang="tr"),
            )
            self.assertNotIn("(press Enter to use)", second.output)

    def test_config_init_default_allows_partial_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "dubbed_video_downloader.cli.shutil.which",
                return_value=None,
            ):
                result = self.runner.invoke(
                    app,
                    ["config", "init", "--default", "--default-lang", "tr"],
                    env={"HOME": tmpdir},
                )
            config_path = (
                Path(tmpdir)
                / ".config"
                / "dubbed-video-downloader"
                / "config.yaml"
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertEqual(
                config_path.read_text(encoding="utf-8"),
                self._expected_config_yaml(default_lang="tr"),
            )

    def test_interactive_init_explicit_lang_skips_language_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "dubbed_video_downloader.cli._stdin_is_interactive",
                return_value=True,
            ):
                result = self.runner.invoke(
                    app,
                    ["init", "--default-lang", "tr"],
                    input="\n\n\n\n\n\n\n\n",
                    env={"HOME": tmpdir},
                )
            config_path = (
                Path(tmpdir)
                / ".config"
                / "dubbed-video-downloader"
                / "config.yaml"
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("default_lang: tr\n", config_path.read_text(encoding="utf-8"))
            self.assertNotIn(
                "Dub language code to use when --lang is omitted.",
                result.output,
            )
            self.assertEqual(result.output.count("(press Enter to use)"), 8)

    def test_init_refuses_overwrite_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            first = self.runner.invoke(app, ["init"], env={"HOME": tmpdir})
            second = self.runner.invoke(app, ["init"], env={"HOME": tmpdir})

        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(second.exit_code, 1, second.output)
        self.assertIn("--force", second.output)
        self.assertNotIn("Output directory", second.output)
        self.assertNotIn("(press Enter to use)", second.output)

    def test_interactive_init_refuses_overwrite_before_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            first = self.runner.invoke(app, ["init"], env={"HOME": tmpdir})
            with patch(
                "dubbed_video_downloader.cli._stdin_is_interactive",
                return_value=True,
            ):
                second = self.runner.invoke(
                    app,
                    ["init"],
                    input="\n\n\n\n\n\n\n\n\n",
                    env={"HOME": tmpdir},
                )

        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(second.exit_code, 1, second.output)
        self.assertIn("--force", second.output)
        self.assertNotIn("Output directory", second.output)
        self.assertNotIn("(press Enter to use)", second.output)

    def test_interactive_init_explains_each_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "dubbed_video_downloader.cli._stdin_is_interactive",
                return_value=True,
            ):
                result = self.runner.invoke(
                    app,
                    ["init"],
                    input="\n\n\n\n\n\n\n\n\n",
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
                "Downloads will be saved under this directory.",
                result.output,
            )
            self.assertIn(
                "Accepted: absolute path, ~ path, or env-var path.",
                result.output,
            )
            self.assertIn(
                "Executable used to merge video and dubbed audio.",
                result.output,
            )
            self.assertIn(
                "Accepted: `ffmpeg`, `ffmpeg.exe`, or absolute path.",
                result.output,
            )
            self.assertIn(
                "Dub language code to use when --lang is omitted.",
                result.output,
            )
            self.assertIn(
                "Accepted: BCP-47 language code, e.g. en, eng, en-US, tr.",
                result.output,
            )
            self.assertIn("Which type of output to download", result.output)
            self.assertIn("Accepted: `video` | `audio`.", result.output)
            self.assertIn("Which video quality to select", result.output)
            self.assertIn("(`144p`-`8640p`, e.g. `720p`)", result.output)
            self.assertIn("Which dubbed audio quality to select", result.output)
            self.assertIn("Accepted: `best` | `medium` | `low`.", result.output)
            self.assertIn("How many times to retry transient metadata", result.output)
            self.assertIn(
                "Accepted: non-negative integer; 0 disables retries.",
                result.output,
            )
            self.assertIn(
                "What to do when the planned output file already exists.",
                result.output,
            )
            self.assertIn("Accepted: `skip` | `fail` | `overwrite`.", result.output)
            self.assertIn(
                "Whether downloads should ask for confirmation after estimating size.",
                result.output,
            )
            self.assertIn("Accepted: `yes` | `no`.", result.output)
            self.assertEqual(result.output.count("(press Enter to use)"), 9)
            self.assertNotIn("Hint:", result.output)
            self.assertIn(
                "Default: ~/Downloads/dbdvdl-output (press Enter to use)",
                result.output,
            )
            self.assertIn("Default: ffmpeg (press Enter to use)", result.output)
            self.assertIn("Default: en (press Enter to use)", result.output)
            self.assertIn("Default: video (press Enter to use)", result.output)
            self.assertIn("Default: best (press Enter to use)", result.output)
            self.assertIn("Default: 3 (press Enter to use)", result.output)
            self.assertIn("Default: skip (press Enter to use)", result.output)
            self.assertIn("Default: false (press Enter to use)", result.output)
            self.assertEqual(
                config_path.read_text(encoding="utf-8"),
                "output_dir: ~/Downloads/dbdvdl-output\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n"
                "default_download_mode: video\n"
                "default_video_quality: best\n"
                "default_audio_quality: best\n"
                "retry_on_network_failure: 3\n"
                "default_exists_behavior: skip\n"
                "ask_for_disk_usage: false\n",
            )

    def test_interactive_init_colors_prompt_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "dubbed_video_downloader.cli._stdin_is_interactive",
                return_value=True,
            ):
                result = self.runner.invoke(
                    app,
                    ["init"],
                    input="\n\n\n\n\n\n\n\n\n",
                    env={"HOME": tmpdir},
                    color=True,
                )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("\x1b[36m\x1b[1mOutput directory", result.output)
        self.assertIn("\x1b[36m\x1b[1mAccepted:", result.output)
        self.assertIn("\x1b[36m\x1b[1mDefault:", result.output)
        self.assertNotIn("\x1b[36m\x1b[1mHint:", result.output)

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
                "default_exists_behavior: skip\n"
                "ask_for_disk_usage: false\n",
            )

    def test_interactive_config_init_explains_prompts_and_keeps_defaults(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "dubbed_video_downloader.cli._stdin_is_interactive",
                return_value=True,
            ):
                result = self.runner.invoke(
                    app,
                    ["config", "init"],
                    input="\n\n\n\n\n\n\n\n\n",
                    env={"HOME": tmpdir},
                )
            config_path = (
                Path(tmpdir)
                / ".config"
                / "dubbed-video-downloader"
                / "config.yaml"
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("Accepted: `video` | `audio`.", result.output)
            self.assertIn("(`144p`-`8640p`, e.g. `720p`)", result.output)
            self.assertEqual(result.output.count("(press Enter to use)"), 9)
            self.assertNotIn("Hint:", result.output)
            self.assertEqual(
                config_path.read_text(encoding="utf-8"),
                "output_dir: ~/Downloads/dbdvdl-output\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n"
                "default_download_mode: video\n"
                "default_video_quality: best\n"
                "default_audio_quality: best\n"
                "retry_on_network_failure: 3\n"
                "default_exists_behavior: skip\n"
                "ask_for_disk_usage: false\n",
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

    def test_init_writes_normalized_default_lang(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(
                app,
                ["init", "--default-lang", "eng"],
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
                "default_lang: en\n",
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

    def test_init_writes_custom_ask_for_disk_usage(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(
                app,
                ["init", "--ask-for-disk-usage"],
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
                "ask_for_disk_usage: true\n",
                config_path.read_text(encoding="utf-8"),
            )

    def test_config_init_writes_custom_ask_for_disk_usage(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(
                app,
                ["config", "init", "--ask-for-disk-usage"],
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
                "ask_for_disk_usage: true\n",
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
        self.assertIn("Ask for disk usage: false", result.output)

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

    def test_config_remove_short_yes_removes_config_directory_non_interactively(
        self,
    ) -> None:
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
                    ["config", "remove", "-y"],
                    env={"HOME": tmpdir},
                )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertFalse(config_dir.exists())
            self.assertIn(f"Removed config directory: {config_dir}", result.output)

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
        plain_output = _plain_cli_output(result.output)

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("dry-run", plain_output)
        self.assertIn("verbose", plain_output)
        self.assertIn("debug", plain_output)
        self.assertIn("mode", plain_output)
        self.assertIn("video-quality", plain_output)
        self.assertIn("audio-quality", plain_output)
        self.assertIn("retry-on-network", plain_output)
        self.assertIn("if-exists", plain_output)
        self.assertIn("yes", plain_output)
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
            output_path = override_output / "en" / "Title.mkv"

            with patch("dubbed_video_downloader.cli.core.download") as download:
                download.return_value = self._download_result_with_file(output_path)
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
            stage_callback=ANY,
            progress_callback=ANY,
        )

    def test_download_interactive_status_passes_stage_callback(self) -> None:
        class FakeDownloadStatusRenderer:
            instances: list[FakeDownloadStatusRenderer] = []

            def __init__(self, console: object, *, enabled: bool) -> None:
                self.enabled = enabled
                self.stages: list[core.DownloadStage] = []
                self.progress_updates: list[core.DownloadProgress] = []
                self.finish_called = False
                self.fail_called = False
                self.instances.append(self)

            def __enter__(self) -> FakeDownloadStatusRenderer:
                return self

            def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
                if exc_type is None:
                    self.finish_called = True
                else:
                    self.fail_called = True

            def update(self, stage: core.DownloadStage) -> None:
                self.stages.append(stage)

            def update_progress(self, progress: core.DownloadProgress) -> None:
                self.progress_updates.append(progress)

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

            with (
                patch(
                    "dubbed_video_downloader.cli._download_status_enabled",
                    return_value=True,
                ),
                patch(
                    "dubbed_video_downloader.cli._DownloadStatusRenderer",
                    FakeDownloadStatusRenderer,
                ),
                patch("dubbed_video_downloader.cli.core.download") as download,
            ):
                download.return_value = self._download_result_with_file(output_path)
                result = self.runner.invoke(
                    app,
                    ["download", "https://www.youtube.com/watch?v=EXAMPLE"],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(len(FakeDownloadStatusRenderer.instances), 2)
        setup_renderer, download_renderer = FakeDownloadStatusRenderer.instances
        self.assertEqual(
            setup_renderer.stages,
            [
                core.DownloadStage.CHECKING_CONFIG,
                core.DownloadStage.PREPARING_OPTIONS,
            ],
        )
        self.assertTrue(setup_renderer.finish_called)
        callback = download.call_args.kwargs["stage_callback"]
        callback(core.DownloadStage.DOWNLOADING_MEDIA)
        self.assertEqual(download_renderer.stages, [core.DownloadStage.DOWNLOADING_MEDIA])
        progress = core.DownloadProgress(
            speed_bytes_per_sec=4_500_000,
            eta_seconds=3897,
            percent=13.0,
        )
        download.call_args.kwargs["progress_callback"](progress)
        self.assertEqual(download_renderer.progress_updates, [progress])
        self.assertTrue(download_renderer.finish_called)

    def test_format_download_progress_helpers(self) -> None:
        progress = core.DownloadProgress(
            speed_bytes_per_sec=4_500_000,
            eta_seconds=3897,
            percent=13.2,
        )
        self.assertEqual(cli._format_download_speed(4_500_000), "4.5 MB/s")
        self.assertEqual(cli._format_download_speed(None), "? MB/s")
        self.assertEqual(cli._format_download_eta(3897), "01:04:57")
        self.assertEqual(cli._format_download_eta(None), "--:--:--")
        self.assertEqual(cli._format_download_percent(13.2), "13% Completed")
        self.assertEqual(cli._format_download_percent(None), "?% Completed")
        self.assertEqual(
            cli._format_download_progress(progress),
            "4.5 MB/s - ETA: 01:04:57 - 13% Completed",
        )

    def test_download_status_renderer_updates_progress_during_download(self) -> None:
        class FakeStatus:
            def __init__(self, text: str, spinner: str) -> None:
                self.text = text
                self.spinner = spinner
                self.started = False
                self.stopped = False
                self.updates: list[str] = []

            def start(self) -> None:
                self.started = True

            def stop(self) -> None:
                self.stopped = True

            def update(self, text: str) -> None:
                self.updates.append(text)

        class FakeConsole:
            def __init__(self) -> None:
                self.prints: list[tuple[str, bool]] = []
                self.statuses: list[FakeStatus] = []

            def print(self, text: str, *, markup: bool) -> None:
                self.prints.append((text, markup))

            def status(self, text: str, *, spinner: str) -> FakeStatus:
                status = FakeStatus(text, spinner)
                self.statuses.append(status)
                return status

        fake_console = FakeConsole()
        renderer = cli._DownloadStatusRenderer(fake_console, enabled=True)
        progress = core.DownloadProgress(
            speed_bytes_per_sec=4_500_000,
            eta_seconds=3897,
            percent=13.0,
        )

        renderer.update(core.DownloadStage.DOWNLOADING_MEDIA)
        with patch("dubbed_video_downloader.cli.time.monotonic", side_effect=[0.0, 0.0, 1.0]):
            renderer.update_progress(progress)
            renderer.update_progress(progress)

        status = fake_console.statuses[0]
        self.assertEqual(
            status.updates,
            [
                "Downloading media...  4.5 MB/s - ETA: 01:04:57 - 13% Completed",
            ],
        )

    def test_download_status_renderer_prints_completed_and_failed_stages(self) -> None:
        class FakeStatus:
            def __init__(self, text: str, spinner: str) -> None:
                self.text = text
                self.spinner = spinner
                self.started = False
                self.stopped = False
                self.updates: list[str] = []

            def start(self) -> None:
                self.started = True

            def stop(self) -> None:
                self.stopped = True

            def update(self, text: str) -> None:
                self.updates.append(text)

        class FakeConsole:
            def __init__(self) -> None:
                self.prints: list[tuple[str, bool]] = []
                self.statuses: list[FakeStatus] = []

            def print(self, text: str, *, markup: bool) -> None:
                self.prints.append((text, markup))

            def status(self, text: str, *, spinner: str) -> FakeStatus:
                status = FakeStatus(text, spinner)
                self.statuses.append(status)
                return status

        fake_console = FakeConsole()
        renderer = cli._DownloadStatusRenderer(fake_console, enabled=True)

        renderer.update(core.DownloadStage.FETCHING_METADATA)
        renderer.update(core.DownloadStage.FETCHING_METADATA)
        renderer.update(core.DownloadStage.DOWNLOADING_MEDIA)
        renderer.fail()

        self.assertEqual(len(fake_console.statuses), 1)
        status = fake_console.statuses[0]
        self.assertEqual(status.text, "Fetching metadata...")
        self.assertEqual(status.spinner, cli.DOWNLOAD_STATUS_SPINNER)
        self.assertTrue(status.started)
        self.assertTrue(status.stopped)
        self.assertEqual(status.updates, ["Downloading media..."])
        self.assertEqual(
            fake_console.prints,
            [
                ("[done] Fetching metadata...", False),
                ("[failed] Downloading media...", False),
            ],
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
            output_path = home / "Downloads" / "from-config" / "en" / "Title.webm"

            with patch("dubbed_video_downloader.cli.core.download") as download:
                download.return_value = self._download_result_with_file(output_path)
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
            output_path = home / "Downloads" / "from-config" / "en" / "Title.mkv"

            with patch("dubbed_video_downloader.cli.core.download") as download:
                download.return_value = self._download_result_with_file(output_path)
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
            output_path = home / "Downloads" / "from-config" / "en" / "Title.mkv"

            with patch("dubbed_video_downloader.cli.core.download") as download:
                download.return_value = self._download_result_with_file(output_path)
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
        self.assertNotIn("Saved to", result.output)
        self.assertNotIn("Size:", result.output)
        download.assert_called_once()

    def test_download_prompts_for_estimated_disk_usage_when_enabled(self) -> None:
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
                "ask_for_disk_usage: true\n",
                encoding="utf-8",
            )
            output_path = home / "Downloads" / "from-config" / "en" / "Title.mkv"
            approved: list[bool] = []

            def fake_download(**kwargs):
                plan = core.DownloadPlan(
                    url=kwargs["url"],
                    lang=kwargs["lang"],
                    resolved_lang=kwargs["lang"],
                    title="Title",
                    uploader="Channel",
                    available_langs=("en",),
                    output_path=output_path,
                    estimated_size_bytes=139_000_000,
                )
                approved.append(kwargs["approval_callback"](plan))
                return self._download_result_with_file(
                    output_path,
                    size_bytes=1_500_000,
                )

            with patch(
                "dubbed_video_downloader.cli._stdin_is_interactive",
                return_value=True,
            ):
                with patch(
                    "dubbed_video_downloader.cli.core.download",
                    side_effect=fake_download,
                ) as download:
                    result = self.runner.invoke(
                        app,
                        ["download", "https://www.youtube.com/watch?v=EXAMPLE"],
                        input="y\n",
                        env={"HOME": tmpdir},
                    )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("~139 MB", result.output)
        self.assertIn("Finished", result.output)
        self.assertIn(f"Saved to {output_path.resolve()}", result.output)
        self.assertIn("Size: 1.5 MB", result.output)
        self.assertEqual(approved, [True])
        download.assert_called_once()

    def test_download_reports_missing_output_file_after_success(self) -> None:
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
                return_value=core.DownloadResult(output_path=output_path),
            ) as download:
                result = self.runner.invoke(
                    app,
                    ["download", "https://www.youtube.com/watch?v=EXAMPLE"],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("Finished", result.output)
        self.assertIn("output file is missing", result.output)
        self.assertNotIn("Saved to", result.output)
        self.assertNotIn("Size:", result.output)
        download.assert_called_once()

    def test_download_decline_disk_usage_prompt_cancels_url(self) -> None:
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
                "ask_for_disk_usage: true\n",
                encoding="utf-8",
            )
            output_path = home / "Downloads" / "from-config" / "en" / "Title.mkv"

            def fake_download(**kwargs):
                plan = core.DownloadPlan(
                    url=kwargs["url"],
                    lang=kwargs["lang"],
                    resolved_lang=kwargs["lang"],
                    title="Title",
                    uploader="Channel",
                    available_langs=("en",),
                    output_path=output_path,
                    estimated_size_bytes=None,
                )
                if kwargs["approval_callback"](plan):
                    return core.DownloadResult(output_path=output_path)
                return core.DownloadResult(
                    status=core.DownloadStatus.CANCELLED,
                    output_path=output_path,
                )

            with patch(
                "dubbed_video_downloader.cli._stdin_is_interactive",
                return_value=True,
            ):
                with patch(
                    "dubbed_video_downloader.cli.core.download",
                    side_effect=fake_download,
                ) as download:
                    result = self.runner.invoke(
                        app,
                        ["download", "https://www.youtube.com/watch?v=EXAMPLE"],
                        input="n\n",
                        env={"HOME": tmpdir},
                    )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("could not be estimated", result.output)
        self.assertIn("Cancelled", result.output)
        self.assertNotIn("Finished", result.output)
        self.assertNotIn("Saved to", result.output)
        self.assertNotIn("Size:", result.output)
        download.assert_called_once()

    def test_download_yes_bypasses_disk_usage_prompt(self) -> None:
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
                "ask_for_disk_usage: true\n",
                encoding="utf-8",
            )
            output_path = home / "Downloads" / "from-config" / "en" / "Title.mkv"

            with patch(
                "dubbed_video_downloader.cli._stdin_is_interactive",
                return_value=False,
            ):
                with patch("dubbed_video_downloader.cli.core.download") as download:
                    download.return_value = self._download_result_with_file(output_path)
                    result = self.runner.invoke(
                        app,
                        [
                            "download",
                            "https://www.youtube.com/watch?v=EXAMPLE",
                            "--yes",
                        ],
                        env={"HOME": tmpdir},
                    )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertNotIn("approval_callback", download.call_args.kwargs)

    def test_download_refuses_non_interactive_disk_usage_prompt_without_yes(
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
                "ask_for_disk_usage: true\n",
                encoding="utf-8",
            )

            with patch(
                "dubbed_video_downloader.cli._stdin_is_interactive",
                return_value=False,
            ):
                with patch("dubbed_video_downloader.cli.core.download") as download:
                    result = self.runner.invoke(
                        app,
                        ["download", "https://www.youtube.com/watch?v=EXAMPLE"],
                        env={"HOME": tmpdir},
                    )

        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("--yes", result.output)
        download.assert_not_called()

    def test_download_keyboard_interrupt_exits_without_finished_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = (
                Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: en\n",
                encoding="utf-8",
            )

            with patch(
                "dubbed_video_downloader.cli.core.download",
                side_effect=KeyboardInterrupt,
            ):
                result = self.runner.invoke(
                    app,
                    ["download", "https://www.youtube.com/watch?v=EXAMPLE"],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 130, result.output)
        self.assertIn("==> Downloading:", result.output)
        self.assertNotIn("Finished", result.output)

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
        self.assertIn("if-exists", _plain_cli_output(result.output))
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

    def test_download_dry_run_ignores_non_interactive_disk_usage_confirmation(
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
                "ask_for_disk_usage: true\n",
                encoding="utf-8",
            )

            with patch(
                "dubbed_video_downloader.cli._stdin_is_interactive",
                return_value=False,
            ):
                with patch(
                    "dubbed_video_downloader.cli.core.plan_download",
                    return_value=core.DownloadPlan(
                        url="https://www.youtube.com/watch?v=EXAMPLE",
                        lang="en",
                        resolved_lang="en",
                        title="Title",
                        uploader="Channel",
                        available_langs=("en",),
                        output_path=home / "Downloads" / "from-config" / "Title.mkv",
                        estimated_size_bytes=10_000_000,
                    ),
                ) as plan:
                    result = self.runner.invoke(
                        app,
                        [
                            "download",
                            "https://www.youtube.com/watch?v=EXAMPLE",
                            "--dry-run",
                        ],
                        env={"HOME": tmpdir},
                    )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Estimated disk usage: ~10 MB", result.output)
        plan.assert_called_once()

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
        self.assertIn("mode", result.output)
        self.assertIn("mp3", result.output)
        download.assert_not_called()

    def test_download_rejects_invalid_lang_before_network_work(self) -> None:
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
                        "--lang",
                        "jp",
                    ],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("Input error:", result.output)
        self.assertIn("--lang", result.output)
        self.assertNotIn("default_lang", result.output)
        self.assertNotIn("Config error:", result.output)
        download.assert_not_called()

    def test_qualities_rejects_invalid_lang_before_network_work(self) -> None:
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

            with patch("dubbed_video_downloader.cli.core.get_quality_report") as report:
                result = self.runner.invoke(
                    app,
                    [
                        "qualities",
                        "https://www.youtube.com/watch?v=EXAMPLE",
                        "--lang",
                        "jp",
                    ],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("Input error:", result.output)
        self.assertIn("--lang", result.output)
        self.assertNotIn("default_lang", result.output)
        self.assertNotIn("Config error:", result.output)
        report.assert_not_called()

    def test_download_allows_lang_override_with_invalid_default_lang_in_config(
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
                "default_lang: jp\n",
                encoding="utf-8",
            )

            with (
                patch("dubbed_video_downloader.cli.core.download") as download,
                patch(
                    "dubbed_video_downloader.cli.core.plan_download",
                    return_value=core.DownloadPlan(
                        url="https://www.youtube.com/watch?v=EXAMPLE",
                        lang="tr",
                        resolved_lang="tr",
                        title="Title",
                        uploader="Channel",
                        available_langs=("tr",),
                        output_path=home / "Downloads" / "from-config" / "tr" / "Title.mkv",
                    ),
                ),
            ):
                result = self.runner.invoke(
                    app,
                    [
                        "download",
                        "https://www.youtube.com/watch?v=EXAMPLE",
                        "--lang",
                        "tr",
                        "--dry-run",
                    ],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertNotIn("Config error:", result.output)
        download.assert_not_called()

    def test_download_rejects_invalid_default_lang_when_lang_not_overridden(
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
                "default_lang: jp\n",
                encoding="utf-8",
            )

            with patch("dubbed_video_downloader.cli.core.download") as download:
                result = self.runner.invoke(
                    app,
                    ["download", "https://www.youtube.com/watch?v=EXAMPLE"],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("Config error:", result.output)
        self.assertIn("default_lang", result.output)
        download.assert_not_called()

    def test_langs_works_with_invalid_default_lang_in_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = (
                home / ".config" / "dubbed-video-downloader" / "config.yaml"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "output_dir: ~/Downloads/from-config\n"
                "ffmpeg_path: ffmpeg\n"
                "default_lang: jp\n",
                encoding="utf-8",
            )

            with patch(
                "dubbed_video_downloader.cli.core.get_audio_language_inventory_for_url",
                return_value=_audio_inventory("tr", "en"),
            ):
                result = self.runner.invoke(
                    app,
                    ["langs", "https://www.youtube.com/watch?v=EXAMPLE"],
                    env={"HOME": tmpdir},
                )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertNotIn("Config error:", result.output)
        self.assertIn("en", result.output)
        self.assertIn("tr", result.output)

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
                        resolved_lang="en",
                        download_mode=core.DownloadMode.AUDIO,
                        title="Title",
                        uploader="Channel",
                        available_langs=("en", "tr"),
                        output_path=planned_output,
                        estimated_size_bytes=139_000_000,
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
        self.assertIn("Estimated disk usage: ~139 MB", result.output)

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
                    resolved_lang="en",
                    download_mode=core.DownloadMode.VIDEO,
                    title="Title",
                    uploader="Channel",
                    available_langs=("en",),
                    output_path=home / "Downloads" / "from-config" / "en" / "Title.mkv",
                    estimated_size_bytes=None,
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
        self.assertIn("Estimated disk usage: ", result.output)
        self.assertIn("unknown", result.output)
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
                    resolved_lang="en",
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
                    resolved_lang="en",
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
                "dubbed_video_downloader.cli.core.get_audio_language_inventory_for_url"
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
        plain_output = _plain_cli_output(result.output)

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("verbose", plain_output)
        self.assertIn("debug", plain_output)
        self.assertIn("retry-on-network", plain_output)

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
                "dubbed_video_downloader.cli.core.get_audio_language_inventory_for_url",
                return_value=_audio_inventory("tr", "en"),
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
                "dubbed_video_downloader.cli.core.get_audio_language_inventory_for_url",
                return_value=_audio_inventory("tr"),
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
                "dubbed_video_downloader.cli.core.get_audio_language_inventory_for_url",
                return_value=_audio_inventory("tr"),
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
                "dubbed_video_downloader.cli.core.get_audio_language_inventory_for_url",
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
                "dubbed_video_downloader.cli.core.get_audio_language_inventory_for_url",
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
                    resolved_lang="tr",
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
