"""Shared helpers for local live integration tests."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from dubbed_video_downloader import core, errors, languages

LIVE_TEST_URL_ENV = "DBDVDL_LIVE_TEST_URL"
LIVE_TEST_LANG_ENV = "DBDVDL_LIVE_TEST_LANG"
NETWORK_ALLOW_ENV = "DBDVDL_TESTS_ALLOW_NETWORK"

MIN_DUBBED_LANG_COUNT = 2

UNAVAILABLE_LANGUAGE_CANDIDATES = ("haw", "sw", "zu", "cy", "gd")


def require_live_test_url() -> str:
    url = os.environ.get(LIVE_TEST_URL_ENV, "").strip()
    if not url:
        pytest.skip(
            f"Set {LIVE_TEST_URL_ENV} to run live integration tests "
            "(see CONTRIBUTING.md)."
        )
    return url


def optional_live_test_lang_override() -> str | None:
    value = os.environ.get(LIVE_TEST_LANG_ENV, "").strip()
    return value or None


def enable_live_network() -> None:
    os.environ[NETWORK_ALLOW_ENV] = "1"


def require_runtime_prerequisites() -> None:
    if shutil.which("ffmpeg") is None:
        pytest.skip("FFmpeg is required for live integration tests.")
    if shutil.which("node") is None:
        pytest.skip("Node.js is required for live integration tests.")


def select_live_test_lang(
    inventory: languages.AudioLanguageInventory,
    *,
    override: str | None = None,
) -> str:
    displayed = languages.display_language_tags(inventory.langs)
    if len(displayed) < MIN_DUBBED_LANG_COUNT:
        pytest.skip(
            f"Live test video must expose at least {MIN_DUBBED_LANG_COUNT} "
            "dubbed audio languages."
        )
    if override is not None:
        normalized_override = languages.normalize_language_code(
            override,
            field=LIVE_TEST_LANG_ENV,
        )
        resolved = languages.resolve_language_for_video(
            normalized_override,
            inventory,
        )
        return resolved
    return displayed[0]


def unavailable_language(inventory: languages.AudioLanguageInventory) -> str:
    available = {languages.format_language_for_display(tag) for tag in inventory.langs}
    for candidate in UNAVAILABLE_LANGUAGE_CANDIDATES:
        try:
            normalized = languages.normalize_language_code(candidate)
        except errors.InvalidLanguageCodeError:
            continue
        if normalized not in available:
            return normalized
    pytest.fail("Could not determine an unavailable language for the live test video.")


def write_live_config(
    config_path: Path,
    output_dir: Path,
    *,
    default_lang: str,
) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        f"output_dir: {output_dir}\n"
        "ffmpeg_path: ffmpeg\n"
        f"default_lang: {default_lang}\n"
        "default_download_mode: video\n"
        "default_video_quality: best\n"
        "default_audio_quality: best\n"
        "retry_on_network_failure: 3\n"
        "default_exists_behavior: skip\n"
        "ask_for_disk_usage: false\n",
        encoding="utf-8",
    )


def incomplete_downloads_dir(output_dir: Path) -> Path:
    return core._incomplete_downloads_dir(output_dir)


def assert_no_stale_incomplete_runs(output_dir: Path) -> None:
    incomplete_dir = incomplete_downloads_dir(output_dir)
    if not incomplete_dir.exists():
        return
    leftover = [path for path in incomplete_dir.iterdir() if path.is_dir()]
    assert not leftover, f"Stale incomplete download runs found: {leftover}"


def assert_output_under_language_dir(
    output_path: Path,
    lang: str,
    output_dir: Path,
) -> None:
    assert output_path.is_file(), f"Expected output file at {output_path}"
    assert output_path.stat().st_size > 0, "Downloaded file must be non-empty"
    relative = output_path.relative_to(output_dir)
    assert relative.parts[0] == lang, (
        f"Expected language directory {lang!r} in output path {relative}"
    )
