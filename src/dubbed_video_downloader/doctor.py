from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def run_checks() -> list[CheckResult]:
    """Return environment checks needed by the downloader."""
    return [
        _python_check(),
        _node_check(),
        _ffmpeg_check(),
        _package_check("yt-dlp"),
        _package_check("yt-dlp-ejs"),
    ]


def _python_check() -> CheckResult:
    return CheckResult(
        name="Python",
        ok=True,
        detail=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    )


def _node_check() -> CheckResult:
    return _command_check("Node", "node", ["node", "--version"])


def _ffmpeg_check() -> CheckResult:
    return _command_check("FFmpeg", "ffmpeg", ["ffmpeg", "-version"])


def _package_check(package_name: str) -> CheckResult:
    try:
        package_version = version(package_name)
    except PackageNotFoundError:
        return CheckResult(package_name, False, "package is not installed")
    return CheckResult(package_name, True, package_version)


def _command_check(name: str, executable: str, command: list[str]) -> CheckResult:
    path = shutil.which(executable)
    if not path:
        return CheckResult(name, False, f"{executable} was not found on PATH")

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
            text=True,
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        return CheckResult(name, False, f"{path} timed out")

    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip().splitlines()
        message = detail[0] if detail else f"{path} exited with code {completed.returncode}"
        return CheckResult(name, False, message)

    first_line = completed.stdout.strip().splitlines()[0]
    return CheckResult(name, True, _format_command_detail(name, first_line, path))


def _format_command_detail(name: str, first_line: str, path: str) -> str:
    if name == "FFmpeg":
        parts = first_line.split()
        version_text = parts[2] if len(parts) >= 3 else first_line
        return f"{version_text} ({path})"
    return f"{first_line} ({path})"
