from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from . import config


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def run_checks(config_path: Path | None = None) -> list[CheckResult]:
    """Return environment checks needed by the downloader."""
    config_result, app_config = _config_check(config_path)
    return [
        _python_check(),
        config_result,
        (
            _output_dir_check(app_config.output_dir)
            if app_config
            else _blocked_check("Output directory")
        ),
        _ffmpeg_check(app_config.ffmpeg_path)
        if app_config
        else _blocked_check("FFmpeg"),
        _node_check(),
        _package_check("yt-dlp"),
        _package_check("yt-dlp-ejs"),
    ]


def _python_check() -> CheckResult:
    ok = sys.version_info >= (3, 10)
    return CheckResult(
        name="Python",
        ok=ok,
        detail=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    )


def _node_check() -> CheckResult:
    return _command_check("Node", "node", ["--version"])


def _ffmpeg_check(ffmpeg_path: str) -> CheckResult:
    return _command_check("FFmpeg", ffmpeg_path, ["-version"])


def _config_check(
    config_path: Path | None = None,
) -> tuple[CheckResult, config.AppConfig | None]:
    path = config_path or config.get_config_path()
    try:
        app_config = config.load_config(path)
    except config.ConfigError as exc:
        return CheckResult("Config", False, str(exc)), None
    return CheckResult("Config", True, str(path)), app_config


def _output_dir_check(output_dir: Path) -> CheckResult:
    if output_dir.exists():
        if not output_dir.is_dir():
            return CheckResult("Output directory", False, f"{output_dir} is not a directory")
        if not _is_writable(output_dir):
            return CheckResult("Output directory", False, f"{output_dir} is not writable")
        return CheckResult("Output directory", True, f"{output_dir} exists and is writable")

    parent = output_dir.parent
    while not parent.exists() and parent != parent.parent:
        parent = parent.parent

    if not parent.exists() or not parent.is_dir():
        return CheckResult(
            "Output directory",
            False,
            f"{output_dir} cannot be created because no parent directory exists",
        )
    if not _is_writable(parent):
        return CheckResult(
            "Output directory",
            False,
            f"{output_dir} cannot be created because {parent} is not writable",
        )
    return CheckResult("Output directory", True, f"{output_dir} can be created")


def _blocked_check(name: str) -> CheckResult:
    return CheckResult(name, False, "config unavailable")


def _package_check(package_name: str) -> CheckResult:
    try:
        package_version = version(package_name)
    except PackageNotFoundError:
        return CheckResult(package_name, False, "package is not installed")
    return CheckResult(package_name, True, package_version)


def _command_check(name: str, executable: str, args: list[str]) -> CheckResult:
    path, error = _resolve_executable(executable)
    if error:
        return CheckResult(name, False, error)

    try:
        completed = subprocess.run(
            [path, *args],
            capture_output=True,
            check=False,
            text=True,
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        return CheckResult(name, False, f"{path} timed out")
    except OSError as exc:
        return CheckResult(name, False, f"{path} could not be run: {exc}")

    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip().splitlines()
        message = detail[0] if detail else f"{path} exited with code {completed.returncode}"
        return CheckResult(name, False, message)

    output_lines = completed.stdout.strip().splitlines()
    first_line = output_lines[0] if output_lines else f"{path} exited successfully"
    return CheckResult(name, True, _format_command_detail(name, first_line, path))


def _resolve_executable(executable: str) -> tuple[str, str | None]:
    path = Path(executable)
    if path.is_absolute():
        if not path.exists():
            return "", f"{path} does not exist"
        if not path.is_file():
            return "", f"{path} is not a file"
        if not _is_executable(path):
            return "", f"{path} is not executable"
        return str(path), None

    resolved = shutil.which(executable)
    if not resolved:
        return "", f"{executable} was not found on PATH"
    return resolved, None


def _is_executable(path: Path) -> bool:
    return path.exists() and path.is_file() and os.access(path, os.X_OK)


def _is_writable(path: Path) -> bool:
    return path.exists() and path.is_dir() and os.access(path, os.W_OK)


def _format_command_detail(name: str, first_line: str, path: str) -> str:
    if name == "FFmpeg":
        parts = first_line.split()
        version_text = parts[2] if len(parts) >= 3 else first_line
        return f"{version_text} ({path})"
    return f"{first_line} ({path})"
