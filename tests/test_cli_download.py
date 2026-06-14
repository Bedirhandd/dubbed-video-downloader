from __future__ import annotations

from pathlib import Path
from typing import ClassVar
from unittest.mock import patch

from typer.testing import CliRunner

from dubbed_video_downloader import cli, config, core, errors, quality
from dubbed_video_downloader.cli import app
from tests.conftest import download_result_with_file
from tests.support.cli_helpers import plain_cli_output


def test_download_allows_lang_override_with_invalid_default_lang_in_config(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: jp\n",
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
        result = cli_runner.invoke(
            app,
            [
                "download",
                "https://www.youtube.com/watch?v=EXAMPLE",
                "--lang",
                "tr",
                "--dry-run",
            ],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 0, result.output
    assert "Config error:" not in result.output
    download.assert_not_called()


def test_download_debug_passes_through_to_core_download(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\n",
        encoding="utf-8",
    )
    output_path = home / "Downloads" / "from-config" / "en" / "Title.mkv"
    with patch("dubbed_video_downloader.cli.core.download") as download:
        download.return_value = download_result_with_file(output_path)
        result = cli_runner.invoke(
            app,
            ["download", "https://www.youtube.com/watch?v=EXAMPLE", "--debug"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 0, result.output
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


def test_download_decline_disk_usage_prompt_cancels_url(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\nask_for_disk_usage: true\n",
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
            status=core.DownloadStatus.CANCELLED, output_path=output_path
        )

    with (
        patch("dubbed_video_downloader.cli._stdin_is_interactive", return_value=True),
        patch(
            "dubbed_video_downloader.cli.core.download", side_effect=fake_download
        ) as download,
    ):
        result = cli_runner.invoke(
            app,
            ["download", "https://www.youtube.com/watch?v=EXAMPLE"],
            input="n\n",
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 0, result.output
    assert "could not be estimated" in result.output
    assert "Cancelled" in result.output
    assert "Finished" not in result.output
    assert "Saved to" not in result.output
    assert "Size:" not in result.output
    download.assert_called_once()


def test_download_dry_run_fails_when_existing_output_policy_is_fail(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\ndefault_exists_behavior: fail\n",
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
        result = cli_runner.invoke(
            app,
            ["download", "https://www.youtube.com/watch?v=EXAMPLE", "--dry-run"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 1, result.output
    assert f"Output: {output_path}" in result.output
    assert "If output exists: fail" in result.output
    assert "Output exists: yes" in result.output
    assert "Error: Output already exists" in result.output


def test_download_dry_run_ignores_non_interactive_disk_usage_confirmation(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\nask_for_disk_usage: true\n",
        encoding="utf-8",
    )
    with (
        patch("dubbed_video_downloader.cli._stdin_is_interactive", return_value=False),
        patch(
            "dubbed_video_downloader.cli.core.plan_download",
            return_value=core.DownloadPlan(
                url="https://www.youtube.com/watch?v=EXAMPLE",
                lang="en",
                resolved_lang="en",
                title="Title",
                uploader="Channel",
                available_langs=("en",),
                output_path=home / "Downloads" / "from-config" / "Title.mkv",
                estimated_size_bytes=10000000,
            ),
        ) as plan,
    ):
        result = cli_runner.invoke(
            app,
            ["download", "https://www.youtube.com/watch?v=EXAMPLE", "--dry-run"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 0, result.output
    assert "Estimated disk usage: ~10 MB" in result.output
    plan.assert_called_once()


def test_download_dry_run_reports_plan_failures(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\n",
        encoding="utf-8",
    )
    with (
        patch("dubbed_video_downloader.cli.core.download") as download,
        patch(
            "dubbed_video_downloader.cli.core.plan_download",
            side_effect=errors.DownloadError("missing language"),
        ) as plan,
    ):
        result = cli_runner.invoke(
            app,
            ["download", "https://www.youtube.com/watch?v=EXAMPLE", "--dry-run"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 1, result.output
    plan.assert_called_once()
    download.assert_not_called()
    assert "Error: missing language" in result.output
    assert "Traceback" not in result.output


def test_download_dry_run_reports_traceback_with_debug(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\n",
        encoding="utf-8",
    )
    with (
        patch("dubbed_video_downloader.cli.core.download") as download,
        patch(
            "dubbed_video_downloader.cli.core.plan_download",
            side_effect=errors.DownloadError("missing language"),
        ) as plan,
    ):
        result = cli_runner.invoke(
            app,
            [
                "download",
                "https://www.youtube.com/watch?v=EXAMPLE",
                "--dry-run",
                "--debug",
            ],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 1, result.output
    plan.assert_called_once()
    download.assert_not_called()
    assert "Error: missing language" in result.output
    assert "Traceback" in result.output


def test_download_dry_run_requires_config_before_network_work(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    with patch("dubbed_video_downloader.cli.core.plan_download") as plan:
        result = cli_runner.invoke(
            app,
            ["download", "https://www.youtube.com/watch?v=EXAMPLE", "--dry-run"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 1, result.output
    assert "dbdvdl init" in result.output
    plan.assert_not_called()


def test_download_dry_run_uses_color_when_enabled(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\n",
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
        result = cli_runner.invoke(
            app,
            ["download", "https://www.youtube.com/watch?v=EXAMPLE", "--dry-run"],
            env={"HOME": str(tmpdir)},
            color=True,
        )
    assert result.exit_code == 0, result.output
    assert "\x1b[" in result.output
    assert "Title: " in result.output
    assert "Channel: " in result.output
    assert "Estimated disk usage: " in result.output
    assert "unknown" in result.output
    assert "Title\n" in result.output


def test_download_dry_run_uses_config_and_allows_cli_overrides(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: tr\ndefault_download_mode: video\nretry_on_network_failure: 4\n",
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
                estimated_size_bytes=139000000,
            ),
        ) as plan,
    ):
        result = cli_runner.invoke(
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
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 0, result.output
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
    assert "Dry run: no files will be downloaded or created." in result.output
    assert "Mode: audio" in result.output
    assert f"Output: {planned_output}" in result.output
    assert "Estimated disk usage: ~139 MB" in result.output


def test_download_dry_run_verbose_passes_through_to_core_plan(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\n",
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
        result = cli_runner.invoke(
            app,
            [
                "download",
                "https://www.youtube.com/watch?v=EXAMPLE",
                "--dry-run",
                "--verbose",
            ],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 0, result.output
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


def test_download_help_includes_dry_run_and_verbose(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(app, ["download", "--help"])
    plain_output = plain_cli_output(result.output)
    assert result.exit_code == 0, result.output
    assert "dry-run" in plain_output
    assert "verbose" in plain_output
    assert "debug" in plain_output
    assert "mode" in plain_output
    assert "video-quality" in plain_output
    assert "audio-quality" in plain_output
    assert "retry-on-network" in plain_output
    assert "if-exists" in plain_output
    assert "yes" in plain_output
    assert "Overrides config" in result.output
    assert "default." in result.output
    assert "[default: tr]" not in result.output


def test_download_interactive_status_passes_stage_callback(
    tmp_path: Path, cli_runner: CliRunner
) -> None:

    class FakeDownloadStatusRenderer:
        instances: ClassVar[list[FakeDownloadStatusRenderer]] = []

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

    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\n",
        encoding="utf-8",
    )
    output_path = home / "Downloads" / "from-config" / "en" / "Title.mkv"
    with (
        patch(
            "dubbed_video_downloader.cli._download_status_enabled", return_value=True
        ),
        patch(
            "dubbed_video_downloader.cli._DownloadStatusRenderer",
            FakeDownloadStatusRenderer,
        ),
        patch("dubbed_video_downloader.cli.core.download") as download,
    ):
        download.return_value = download_result_with_file(output_path)
        result = cli_runner.invoke(
            app,
            ["download", "https://www.youtube.com/watch?v=EXAMPLE"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 0, result.output
    assert len(FakeDownloadStatusRenderer.instances) == 2
    setup_renderer, download_renderer = FakeDownloadStatusRenderer.instances
    assert setup_renderer.stages == [
        core.DownloadStage.CHECKING_CONFIG,
        core.DownloadStage.PREPARING_OPTIONS,
    ]
    assert setup_renderer.finish_called
    callback = download.call_args.kwargs["stage_callback"]
    callback(core.DownloadStage.DOWNLOADING_MEDIA)
    assert download_renderer.stages == [core.DownloadStage.DOWNLOADING_MEDIA]
    progress = core.DownloadProgress(
        speed_bytes_per_sec=4500000, eta_seconds=3897, percent=13.0
    )
    download.call_args.kwargs["progress_callback"](progress)
    assert download_renderer.progress_updates == [progress]
    assert download_renderer.finish_called


def test_download_keyboard_interrupt_exits_without_finished_message(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    config_path = Path(tmpdir) / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\n",
        encoding="utf-8",
    )
    with patch(
        "dubbed_video_downloader.cli.core.download", side_effect=KeyboardInterrupt
    ):
        result = cli_runner.invoke(
            app,
            ["download", "https://www.youtube.com/watch?v=EXAMPLE"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 130, result.output
    assert "==> Downloading:" in result.output
    assert "Finished" not in result.output


def test_download_prompts_for_estimated_disk_usage_when_enabled(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\nask_for_disk_usage: true\n",
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
            estimated_size_bytes=139000000,
        )
        approved.append(kwargs["approval_callback"](plan))
        return download_result_with_file(output_path, size_bytes=1500000)

    with (
        patch("dubbed_video_downloader.cli._stdin_is_interactive", return_value=True),
        patch(
            "dubbed_video_downloader.cli.core.download", side_effect=fake_download
        ) as download,
    ):
        result = cli_runner.invoke(
            app,
            ["download", "https://www.youtube.com/watch?v=EXAMPLE"],
            input="y\n",
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 0, result.output
    assert "~139 MB" in result.output
    assert "Finished" in result.output
    assert f"Saved to {output_path.resolve()}" in result.output
    assert "Size: 1.5 MB" in result.output
    assert approved == [True]
    download.assert_called_once()


def test_download_refuses_non_interactive_disk_usage_prompt_without_yes(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\nask_for_disk_usage: true\n",
        encoding="utf-8",
    )
    with (
        patch("dubbed_video_downloader.cli._stdin_is_interactive", return_value=False),
        patch("dubbed_video_downloader.cli.core.download") as download,
    ):
        result = cli_runner.invoke(
            app,
            ["download", "https://www.youtube.com/watch?v=EXAMPLE"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 1, result.output
    assert "--yes" in result.output
    download.assert_not_called()


def test_download_rejects_invalid_audio_quality_before_network_work(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\n",
        encoding="utf-8",
    )
    with patch("dubbed_video_downloader.cli.core.download") as download:
        result = cli_runner.invoke(
            app,
            [
                "download",
                "https://www.youtube.com/watch?v=EXAMPLE",
                "--audio-quality",
                "128k",
            ],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 1, result.output
    assert "audio_quality" in result.output
    download.assert_not_called()


def test_download_rejects_invalid_default_lang_when_lang_not_overridden(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: jp\n",
        encoding="utf-8",
    )
    with patch("dubbed_video_downloader.cli.core.download") as download:
        result = cli_runner.invoke(
            app,
            ["download", "https://www.youtube.com/watch?v=EXAMPLE"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 1, result.output
    assert "Config error:" in result.output
    assert "default_lang" in result.output
    download.assert_not_called()


def test_download_rejects_invalid_if_exists_before_network_work(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\n",
        encoding="utf-8",
    )
    with patch("dubbed_video_downloader.cli.core.download") as download:
        result = cli_runner.invoke(
            app,
            [
                "download",
                "https://www.youtube.com/watch?v=EXAMPLE",
                "--if-exists",
                "replace",
            ],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 2, result.output
    assert "if-exists" in plain_cli_output(result.output)
    download.assert_not_called()


def test_download_rejects_invalid_lang_before_network_work(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\n",
        encoding="utf-8",
    )
    with patch("dubbed_video_downloader.cli.core.download") as download:
        result = cli_runner.invoke(
            app,
            ["download", "https://www.youtube.com/watch?v=EXAMPLE", "--lang", "jp"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 1, result.output
    assert "Input error:" in result.output
    assert "--lang" in result.output
    assert "default_lang" not in result.output
    assert "Config error:" not in result.output
    download.assert_not_called()


def test_download_rejects_invalid_mode_before_network_work(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\n",
        encoding="utf-8",
    )
    with patch("dubbed_video_downloader.cli.core.download") as download:
        result = cli_runner.invoke(
            app,
            ["download", "https://www.youtube.com/watch?v=EXAMPLE", "--mode", "mp3"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 2, result.output
    assert "mode" in result.output
    assert "mp3" in result.output
    download.assert_not_called()


def test_download_rejects_invalid_video_quality_before_network_work(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\n",
        encoding="utf-8",
    )
    with patch("dubbed_video_downloader.cli.core.download") as download:
        result = cli_runner.invoke(
            app,
            [
                "download",
                "https://www.youtube.com/watch?v=EXAMPLE",
                "--video-quality",
                "-100p",
            ],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 1, result.output
    assert "video_quality" in result.output
    download.assert_not_called()


def test_download_rejects_negative_retry_before_network_work(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\n",
        encoding="utf-8",
    )
    with patch("dubbed_video_downloader.cli.core.download") as download:
        result = cli_runner.invoke(
            app,
            [
                "download",
                "https://www.youtube.com/watch?v=EXAMPLE",
                "--retry-on-network-failure",
                "-1",
            ],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 1, result.output
    assert "retry_on_network_failure" in result.output
    download.assert_not_called()


def test_download_rejects_video_quality_in_audio_mode_before_network_work(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\ndefault_download_mode: audio\n",
        encoding="utf-8",
    )
    with patch("dubbed_video_downloader.cli.core.download") as download:
        result = cli_runner.invoke(
            app,
            [
                "download",
                "https://www.youtube.com/watch?v=EXAMPLE",
                "--video-quality",
                "720p",
            ],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 1, result.output
    assert "--video-quality" in result.output
    download.assert_not_called()


def test_download_reports_missing_output_file_after_success(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\n",
        encoding="utf-8",
    )
    output_path = home / "Downloads" / "from-config" / "en" / "Title.mkv"
    with patch(
        "dubbed_video_downloader.cli.core.download",
        return_value=core.DownloadResult(output_path=output_path),
    ) as download:
        result = cli_runner.invoke(
            app,
            ["download", "https://www.youtube.com/watch?v=EXAMPLE"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 1, result.output
    assert "Finished" in result.output
    assert "output file is missing" in result.output
    assert "Saved to" not in result.output
    assert "Size:" not in result.output
    download.assert_called_once()


def test_download_reports_skipped_result(tmp_path: Path, cli_runner: CliRunner) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\n",
        encoding="utf-8",
    )
    output_path = home / "Downloads" / "from-config" / "en" / "Title.mkv"
    with patch(
        "dubbed_video_downloader.cli.core.download",
        return_value=core.DownloadResult(
            status=core.DownloadStatus.SKIPPED, output_path=output_path
        ),
    ) as download:
        result = cli_runner.invoke(
            app,
            ["download", "https://www.youtube.com/watch?v=EXAMPLE"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 0, result.output
    assert "Skipped" in result.output
    assert f"Output already exists: {output_path}" in result.output
    assert "Saved to" not in result.output
    assert "Size:" not in result.output
    download.assert_called_once()


def test_download_requires_config_before_network_work(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    with patch("dubbed_video_downloader.cli.core.download") as download:
        result = cli_runner.invoke(
            app,
            ["download", "https://www.youtube.com/watch?v=EXAMPLE"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 1, result.output
    assert "dbdvdl init" in result.output
    download.assert_not_called()


def test_download_status_renderer_prints_completed_and_failed_stages() -> None:

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
    assert len(fake_console.statuses) == 1
    status = fake_console.statuses[0]
    assert status.text == "Fetching metadata..."
    assert status.spinner == cli.DOWNLOAD_STATUS_SPINNER
    assert status.started
    assert status.stopped
    assert status.updates == ["Downloading media..."]
    assert fake_console.prints == [
        ("[done] Fetching metadata...", False),
        ("[failed] Downloading media...", False),
    ]


def test_download_status_renderer_updates_progress_during_download() -> None:

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
        speed_bytes_per_sec=4500000, eta_seconds=3897, percent=13.0
    )
    renderer.update(core.DownloadStage.DOWNLOADING_MEDIA)
    with patch(
        "dubbed_video_downloader.cli.time.monotonic", side_effect=[0.0, 0.0, 1.0]
    ):
        renderer.update_progress(progress)
        renderer.update_progress(progress)
    status = fake_console.statuses[0]
    assert status.updates == [
        "Downloading media...  4.5 MB/s - ETA: 01:04:57 - 13% Completed"
    ]


def test_download_uses_config_and_allows_cli_overrides(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: tr\ndefault_download_mode: audio\ndefault_video_quality: low\ndefault_audio_quality: medium\nretry_on_network_failure: 4\ndefault_exists_behavior: fail\n",
        encoding="utf-8",
    )
    override_output = home / "Videos" / "override"
    override_ffmpeg = home / "bin" / "ffmpeg"
    output_path = override_output / "en" / "Title.mkv"
    with (
        patch(
            "dubbed_video_downloader.cli._download_status_enabled", return_value=False
        ),
        patch("dubbed_video_downloader.cli.core.download") as download,
    ):
        download.return_value = download_result_with_file(output_path)
        result = cli_runner.invoke(
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
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 0, result.output
    download.assert_called_once_with(
        url="https://www.youtube.com/watch?v=EXAMPLE",
        lang="en",
        download_mode=core.DownloadMode.VIDEO,
        ffmpeg_path=str(override_ffmpeg),
        output_dir=override_output,
        video_quality=quality.VideoQuality(quality.VideoQualityKind.EXACT, 720),
        audio_quality=quality.AudioQuality(quality.AudioQualityKind.LOW),
        verbose=False,
        debug=False,
        retry_on_network_failure=6,
        exists_behavior=config.FileExistsBehavior.OVERWRITE,
    )


def test_download_uses_config_default_exists_behavior(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\ndefault_exists_behavior: fail\n",
        encoding="utf-8",
    )
    output_path = home / "Downloads" / "from-config" / "en" / "Title.mkv"
    with patch("dubbed_video_downloader.cli.core.download") as download:
        download.return_value = download_result_with_file(output_path)
        result = cli_runner.invoke(
            app,
            ["download", "https://www.youtube.com/watch?v=EXAMPLE"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 0, result.output
    assert (
        download.call_args.kwargs["exists_behavior"] == config.FileExistsBehavior.FAIL
    )


def test_download_verbose_passes_through_to_core_download(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\ndefault_download_mode: audio\n",
        encoding="utf-8",
    )
    output_path = home / "Downloads" / "from-config" / "en" / "Title.webm"
    with patch("dubbed_video_downloader.cli.core.download") as download:
        download.return_value = download_result_with_file(output_path)
        result = cli_runner.invoke(
            app,
            ["download", "https://www.youtube.com/watch?v=EXAMPLE", "--verbose"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 0, result.output
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


def test_download_yes_bypasses_disk_usage_prompt(
    tmp_path: Path, cli_runner: CliRunner
) -> None:
    tmpdir = tmp_path
    home = Path(tmpdir)
    config_path = home / ".config" / "dubbed-video-downloader" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "output_dir: ~/Downloads/from-config\nffmpeg_path: ffmpeg\ndefault_lang: en\nask_for_disk_usage: true\n",
        encoding="utf-8",
    )
    output_path = home / "Downloads" / "from-config" / "en" / "Title.mkv"
    with (
        patch("dubbed_video_downloader.cli._stdin_is_interactive", return_value=False),
        patch("dubbed_video_downloader.cli.core.download") as download,
    ):
        download.return_value = download_result_with_file(output_path)
        result = cli_runner.invoke(
            app,
            ["download", "https://www.youtube.com/watch?v=EXAMPLE", "--yes"],
            env={"HOME": str(tmpdir)},
        )
    assert result.exit_code == 0, result.output
    assert "approval_callback" not in download.call_args.kwargs


def test_format_download_progress_helpers() -> None:
    progress = core.DownloadProgress(
        speed_bytes_per_sec=4500000, eta_seconds=3897, percent=13.2
    )
    assert cli._format_download_speed(4500000) == "4.5 MB/s"
    assert cli._format_download_speed(None) == "? MB/s"
    assert cli._format_download_eta(3897) == "01:04:57"
    assert cli._format_download_eta(None) == "--:--:--"
    assert cli._format_download_percent(13.2) == "13% Completed"
    assert cli._format_download_percent(None) == "?% Completed"
    assert (
        cli._format_download_progress(progress)
        == "4.5 MB/s - ETA: 01:04:57 - 13% Completed"
    )
