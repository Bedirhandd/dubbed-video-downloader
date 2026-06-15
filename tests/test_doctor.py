from __future__ import annotations

import os
import stat
import subprocess
from importlib.metadata import PackageNotFoundError
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from dubbed_video_downloader import doctor
from dubbed_video_downloader.cli import app
from tests.conftest import expected_config_yaml
from tests.support.cli_helpers import plain_cli_output


def fake_completed(
    *,
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["mock"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


@pytest.mark.parametrize(
    ("executable", "setup", "expected_path", "expected_error"),
    [
        ("missing", "missing", "", "{path} does not exist"),
        ("directory", "directory", "", "{path} is not a file"),
        ("not_executable", "not_executable", "", "{path} is not executable"),
        ("executable", "executable", "{path}", None),
    ],
)
def test_resolve_executable_absolute_path(
    tmp_path: Path,
    executable: str,
    setup: str,
    expected_path: str,
    expected_error: str | None,
) -> None:
    if setup == "missing":
        path = tmp_path / "missing-bin"
    elif setup == "directory":
        path = tmp_path / "bin-dir"
        path.mkdir()
    elif setup == "not_executable":
        path = tmp_path / "ffmpeg"
        path.write_text("#!/bin/sh\n", encoding="utf-8")
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    else:
        path = tmp_path / "ffmpeg"
        path.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
        path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

    resolved_path, error = doctor._resolve_executable(str(path))

    if expected_error is None:
        assert resolved_path == expected_path.format(path=path)
        assert error is None
    else:
        assert resolved_path == ""
        assert error == expected_error.format(path=path)


def test_resolve_executable_relative_name_not_on_path() -> None:
    with patch("dubbed_video_downloader.doctor.shutil.which", return_value=None):
        resolved_path, error = doctor._resolve_executable("missing-tool")

    assert resolved_path == ""
    assert error == "missing-tool was not found on PATH"


def test_resolve_executable_relative_name_found_on_path() -> None:
    with patch(
        "dubbed_video_downloader.doctor.shutil.which",
        return_value="/usr/bin/ffmpeg",
    ):
        resolved_path, error = doctor._resolve_executable("ffmpeg")

    assert resolved_path == "/usr/bin/ffmpeg"
    assert error is None


def test_command_check_reports_resolve_error() -> None:
    with patch(
        "dubbed_video_downloader.doctor._resolve_executable",
        return_value=("", "ffmpeg was not found on PATH"),
    ):
        result = doctor._command_check("FFmpeg", "ffmpeg", ["-version"])

    assert result == doctor.CheckResult(
        name="FFmpeg",
        ok=False,
        detail="ffmpeg was not found on PATH",
    )


def test_command_check_successful_node_command() -> None:
    executable = "/usr/bin/node"
    with (
        patch(
            "dubbed_video_downloader.doctor._resolve_executable",
            return_value=(executable, None),
        ),
        patch(
            "dubbed_video_downloader.doctor.subprocess.run",
            return_value=fake_completed(stdout="v22.0.0\n"),
        ),
    ):
        result = doctor._command_check("Node", "node", ["--version"])

    assert result.ok is True
    assert result.detail == f"v22.0.0 ({executable})"


def test_command_check_successful_ffmpeg_uses_third_token() -> None:
    executable = "/usr/bin/ffmpeg"
    with (
        patch(
            "dubbed_video_downloader.doctor._resolve_executable",
            return_value=(executable, None),
        ),
        patch(
            "dubbed_video_downloader.doctor.subprocess.run",
            return_value=fake_completed(
                stdout="ffmpeg version 6.1.1 Copyright (c) 2000-2023\n",
            ),
        ),
    ):
        result = doctor._command_check("FFmpeg", "ffmpeg", ["-version"])

    assert result.ok is True
    assert result.detail == f"6.1.1 ({executable})"


def test_command_check_nonzero_exit_uses_first_stderr_line() -> None:
    executable = "/usr/bin/ffmpeg"
    with (
        patch(
            "dubbed_video_downloader.doctor._resolve_executable",
            return_value=(executable, None),
        ),
        patch(
            "dubbed_video_downloader.doctor.subprocess.run",
            return_value=fake_completed(returncode=1, stderr="broken binary\n"),
        ),
    ):
        result = doctor._command_check("FFmpeg", "ffmpeg", ["-version"])

    assert result.ok is False
    assert result.detail == "broken binary"


def test_command_check_nonzero_exit_without_output() -> None:
    executable = "/usr/bin/ffmpeg"
    with (
        patch(
            "dubbed_video_downloader.doctor._resolve_executable",
            return_value=(executable, None),
        ),
        patch(
            "dubbed_video_downloader.doctor.subprocess.run",
            return_value=fake_completed(returncode=2),
        ),
    ):
        result = doctor._command_check("FFmpeg", "ffmpeg", ["-version"])

    assert result.ok is False
    assert result.detail == f"{executable} exited with code 2"


def test_command_check_timeout() -> None:
    executable = "/usr/bin/node"
    with (
        patch(
            "dubbed_video_downloader.doctor._resolve_executable",
            return_value=(executable, None),
        ),
        patch(
            "dubbed_video_downloader.doctor.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["node"], timeout=5),
        ),
    ):
        result = doctor._command_check("Node", "node", ["--version"])

    assert result.ok is False
    assert result.detail == f"{executable} timed out"


def test_command_check_os_error() -> None:
    executable = "/usr/bin/node"
    with (
        patch(
            "dubbed_video_downloader.doctor._resolve_executable",
            return_value=(executable, None),
        ),
        patch(
            "dubbed_video_downloader.doctor.subprocess.run",
            side_effect=OSError("permission denied"),
        ),
    ):
        result = doctor._command_check("Node", "node", ["--version"])

    assert result.ok is False
    assert result.detail == f"{executable} could not be run: permission denied"


def test_output_dir_check_existing_writable_directory(tmp_path: Path) -> None:
    output_dir = tmp_path / "downloads"
    output_dir.mkdir()

    result = doctor._output_dir_check(output_dir)

    assert result.ok is True
    assert result.detail == f"{output_dir} exists and is writable"


def test_output_dir_check_existing_path_is_file(tmp_path: Path) -> None:
    output_dir = tmp_path / "not-a-dir"
    output_dir.write_text("file", encoding="utf-8")

    result = doctor._output_dir_check(output_dir)

    assert result.ok is False
    assert result.detail == f"{output_dir} is not a directory"


def test_output_dir_check_existing_directory_not_writable(tmp_path: Path) -> None:
    output_dir = tmp_path / "readonly"
    output_dir.mkdir()
    output_dir.chmod(stat.S_IRUSR | stat.S_IXUSR)

    try:
        with patch(
            "dubbed_video_downloader.doctor.os.access",
            side_effect=lambda path, mode: not (path == output_dir and mode == os.W_OK),
        ):
            result = doctor._output_dir_check(output_dir)
    finally:
        output_dir.chmod(stat.S_IRWXU)

    assert result.ok is False
    assert result.detail == f"{output_dir} is not writable"


def test_output_dir_check_missing_directory_with_writable_parent(
    tmp_path: Path,
) -> None:
    parent = tmp_path / "parent"
    parent.mkdir()
    output_dir = parent / "nested" / "downloads"

    result = doctor._output_dir_check(output_dir)

    assert result.ok is True
    assert result.detail == f"{output_dir} can be created"


def test_output_dir_check_walks_up_to_existing_parent(tmp_path: Path) -> None:
    root = tmp_path / "a"
    root.mkdir()
    output_dir = root / "b" / "c" / "downloads"

    result = doctor._output_dir_check(output_dir)

    assert result.ok is True
    assert result.detail == f"{output_dir} can be created"


def test_output_dir_check_parent_is_file(tmp_path: Path) -> None:
    parent_file = tmp_path / "parent-file"
    parent_file.write_text("not a directory", encoding="utf-8")
    output_dir = parent_file / "child"

    result = doctor._output_dir_check(output_dir)

    assert result.ok is False
    assert (
        result.detail
        == f"{output_dir} cannot be created because no parent directory exists"
    )


def test_output_dir_check_parent_not_writable(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    parent.mkdir()
    output_dir = parent / "child"

    with patch(
        "dubbed_video_downloader.doctor.os.access",
        side_effect=lambda path, mode: not (path == parent and mode == os.W_OK),
    ):
        result = doctor._output_dir_check(output_dir)

    assert result.ok is False
    assert result.detail == (
        f"{output_dir} cannot be created because {parent} is not writable"
    )


def test_config_check_valid_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(expected_config_yaml(), encoding="utf-8")

    result, app_config = doctor._config_check(config_path)

    assert result.ok is True
    assert result.detail == str(config_path)
    assert app_config is not None
    assert app_config.default_lang == "en"


def test_config_check_invalid_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("not: [valid", encoding="utf-8")

    result, app_config = doctor._config_check(config_path)

    assert result.ok is False
    assert "Could not parse" in result.detail
    assert app_config is None


@pytest.mark.skipif(os.name != "posix", reason="POSIX permission modes")
def test_config_permissions_check_restrictive(tmp_path: Path) -> None:
    config_dir = tmp_path / "config-dir"
    config_dir.mkdir(mode=0o700)
    config_path = config_dir / "config.yaml"
    config_path.write_text(expected_config_yaml(), encoding="utf-8")
    os.chmod(config_path, 0o600)

    result = doctor._config_permissions_check(config_path)

    assert result.ok is True
    assert result.detail == "owner-only permissions"


@pytest.mark.skipif(os.name != "posix", reason="POSIX permission modes")
def test_config_permissions_check_warns_on_loose_permissions(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(expected_config_yaml(), encoding="utf-8")
    os.chmod(config_path, 0o644)

    result = doctor._config_permissions_check(config_path)

    assert result.ok is True
    assert "permissions are not owner-only" in result.detail
    assert "chmod 600" in result.detail


def test_package_check_installed() -> None:
    with patch(
        "dubbed_video_downloader.doctor.version",
        return_value="2026.3.17",
    ):
        result = doctor._package_check("yt-dlp")

    assert result.ok is True
    assert result.detail == "2026.3.17"


def test_package_check_missing() -> None:
    with patch(
        "dubbed_video_downloader.doctor.version",
        side_effect=PackageNotFoundError("yt-dlp"),
    ):
        result = doctor._package_check("yt-dlp")

    assert result.ok is False
    assert result.detail == "package is not installed"


def test_run_checks_order_and_blocked_dependencies(tmp_path: Path) -> None:
    missing_config = tmp_path / "missing-config.yaml"

    with (
        patch("dubbed_video_downloader.doctor._python_check") as python_check,
        patch("dubbed_video_downloader.doctor._node_check") as node_check,
        patch(
            "dubbed_video_downloader.doctor._config_check",
            return_value=(
                doctor.CheckResult("Config", False, "config missing"),
                None,
            ),
        ),
        patch("dubbed_video_downloader.doctor._package_check") as package_check,
    ):
        python_check.return_value = doctor.CheckResult("Python", True, "3.12.0")
        node_check.return_value = doctor.CheckResult("Node", True, "v22.0.0")
        package_check.side_effect = [
            doctor.CheckResult("yt-dlp", True, "2026.3.17"),
            doctor.CheckResult("yt-dlp-ejs", True, "0.8.0"),
        ]
        results = doctor.run_checks(missing_config)

    assert [result.name for result in results] == [
        "Python",
        "Config",
        "Config permissions",
        "Output directory",
        "FFmpeg",
        "Node",
        "yt-dlp",
        "yt-dlp-ejs",
    ]
    assert results[1].ok is False
    assert results[2] == doctor.CheckResult(
        "Config permissions", False, "config unavailable"
    )
    assert results[3] == doctor.CheckResult(
        "Output directory", False, "config unavailable"
    )
    assert results[4] == doctor.CheckResult("FFmpeg", False, "config unavailable")


def test_run_checks_with_valid_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    output_dir = tmp_path / "output"
    config_path.write_text(
        expected_config_yaml(output_dir=str(output_dir)),
        encoding="utf-8",
    )

    with (
        patch(
            "dubbed_video_downloader.doctor._ffmpeg_check",
            return_value=doctor.CheckResult("FFmpeg", True, "6.1.1"),
        ),
        patch(
            "dubbed_video_downloader.doctor._node_check",
            return_value=doctor.CheckResult("Node", True, "v22.0.0"),
        ),
        patch(
            "dubbed_video_downloader.doctor._package_check",
            side_effect=[
                doctor.CheckResult("yt-dlp", True, "2026.3.17"),
                doctor.CheckResult("yt-dlp-ejs", True, "0.8.0"),
            ],
        ),
    ):
        results = doctor.run_checks(config_path)

    assert all(result.ok for result in results)
    assert results[3].detail == f"{output_dir} can be created"


def test_doctor_command_reports_success(cli_runner: CliRunner) -> None:
    checks = [
        doctor.CheckResult("Python", True, "3.12.0"),
        doctor.CheckResult("Config", True, "/tmp/config.yaml"),
        doctor.CheckResult("Output directory", True, "writable"),
        doctor.CheckResult("FFmpeg", True, "6.1.1"),
        doctor.CheckResult("Node", True, "v22.0.0"),
        doctor.CheckResult("yt-dlp", True, "2026.3.17"),
        doctor.CheckResult("yt-dlp-ejs", True, "0.8.0"),
    ]
    with patch("dubbed_video_downloader.cli.doctor.run_checks", return_value=checks):
        result = cli_runner.invoke(app, ["doctor"])

    assert result.exit_code == 0, result.output
    output = plain_cli_output(result.output)
    assert "System check" in output
    assert "Python" in output and "OK" in output
    assert "FAIL" not in output


def test_doctor_command_exits_nonzero_when_check_fails(cli_runner: CliRunner) -> None:
    checks = [
        doctor.CheckResult("Python", True, "3.12.0"),
        doctor.CheckResult("Config", False, "config missing"),
        doctor.CheckResult("Output directory", False, "config unavailable"),
        doctor.CheckResult("FFmpeg", False, "config unavailable"),
        doctor.CheckResult("Node", True, "v22.0.0"),
        doctor.CheckResult("yt-dlp", True, "2026.3.17"),
        doctor.CheckResult("yt-dlp-ejs", True, "0.8.0"),
    ]
    with patch("dubbed_video_downloader.cli.doctor.run_checks", return_value=checks):
        result = cli_runner.invoke(app, ["doctor"])

    assert result.exit_code == 1, result.output
    output = plain_cli_output(result.output)
    assert "Config" in output and "FAIL" in output
