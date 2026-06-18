from __future__ import annotations

import contextlib
import ctypes
import errno
import json
import os
import platform
import random
import shutil
import signal
import stat
import sys
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, cast

import yt_dlp
from yt_dlp.utils import YoutubeDLError

from . import errors, languages, quality
from .download_mode import DownloadMode, normalize_download_mode
from .exists_behavior import FileExistsBehavior, normalize_exists_behavior
from .yt_dlp_types import InfoDict, YdlParams

DEFAULT_OUTPUT_DIR = Path("Videos")
DEFAULT_MERGE_OUTPUT_FORMAT = "mkv"
DEFAULT_RETRY_ON_NETWORK_FAILURE = 3
DEFAULT_EXISTS_BEHAVIOR = FileExistsBehavior.SKIP
MAX_RETRY_SLEEP_SECONDS = 8.0
FINALIZE_COPY_BUFFER_SIZE = 4 * 1024 * 1024
INCOMPLETE_DOWNLOAD_DIR = Path("tmp") / ".incomplete"
INCOMPLETE_CLEANUP_LOCK_FILENAME = ".cleanup.lock"
RUN_LOCK_FILENAME = ".lock"
RUN_METADATA_FILENAME = "run.json"
RUN_METADATA_APPLICATION = "dubbed-video-downloader"
RUN_METADATA_VERSION = 1
RUN_METADATA_FINALIZING_COPY_DIRS = "finalizing_copy_dirs"
FINALIZING_COPY_DIR_NAME = ".dubbed-video-downloader-finalizing"
FINALIZING_COPY_DIR_MODE = 0o700
_CLEANUP_FINALIZING_COPY_SUPPORTS_DIR_FD = (
    os.open in os.supports_dir_fd
    and os.stat in os.supports_dir_fd
    and os.unlink in os.supports_dir_fd
    and hasattr(os, "fchmod")
)
FALLBACK_FINALIZE_COPY_MARKER = ".finalizing-copy"
AT_FDCWD = -100
LINUX_RENAME_NOREPLACE = 1
DARWIN_RENAME_EXCL = 0x00000004
WINDOWS_MOVEFILE_WRITE_THROUGH = 0x00000008
WINDOWS_ERROR_FILE_EXISTS = 80
WINDOWS_ERROR_ALREADY_EXISTS = 183
WINDOWS_ERROR_NOT_SAME_DEVICE = 17
WINDOWS_ERROR_CALL_NOT_IMPLEMENTED = 120
LINUX_RENAMEAT2_SYSCALL_NUMBERS = {
    "x86_64": 316,
    "amd64": 316,
    "i386": 353,
    "i686": 353,
    "aarch64": 276,
    "arm64": 276,
    "armv7l": 382,
    "armv6l": 382,
    "riscv64": 276,
}


class _MsvcrtModule(Protocol):
    LK_LOCK: int
    LK_NBLCK: int
    LK_UNLCK: int

    def locking(self, fd: int, mode: int, nbytes: int) -> None: ...


class _WindowsCtypesModule(Protocol):
    FormatError: Callable[[int], str]

    def WinDLL(self, name: str, *, use_last_error: bool = ...) -> Any: ...
    def set_last_error(self, code: int) -> None: ...
    def get_last_error(self) -> int: ...


class _UnsafeStagingPathError(OSError):
    pass


class _AtomicNoClobberPublishUnsupportedError(OSError):
    pass


class DownloadStatus(str, Enum):
    DOWNLOADED = "downloaded"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class DownloadStage(str, Enum):
    CHECKING_CONFIG = "checking_config"
    PREPARING_OPTIONS = "preparing_options"
    FETCHING_METADATA = "fetching_metadata"
    CHECKING_LANGUAGES = "checking_languages"
    SELECTING_QUALITIES = "selecting_qualities"
    PLANNING_OUTPUT = "planning_output"
    PREPARING_OUTPUT_DIR = "preparing_output_dir"
    DOWNLOADING_MEDIA = "downloading_media"
    MERGING_MEDIA = "merging_media"
    FINALIZING_OUTPUT = "finalizing_output"
    SKIPPING_EXISTING_OUTPUT = "skipping_existing_output"


DownloadStageCallback = Callable[[DownloadStage], None]
DownloadProgressCallback = Callable[["DownloadProgress"], None]
DownloadApprovalCallback = Callable[["DownloadPlan"], bool]


@dataclass(frozen=True)
class DownloadProgress:
    speed_bytes_per_sec: float | None
    eta_seconds: int | None
    percent: float | None


@dataclass(frozen=True)
class DownloadPlan:
    url: str
    lang: str
    resolved_lang: str
    title: str | None
    uploader: str | None
    available_langs: tuple[str, ...]
    output_path: Path
    download_mode: DownloadMode = DownloadMode.VIDEO
    video_quality: str | None = None
    selected_video_quality: str | None = None
    audio_quality: str = quality.DEFAULT_AUDIO_QUALITY.label
    selected_audio_quality: str = quality.DEFAULT_AUDIO_QUALITY.label
    quality_notes: tuple[str, ...] = ()
    exists_behavior: FileExistsBehavior = DEFAULT_EXISTS_BEHAVIOR
    output_exists: bool = False
    estimated_size_bytes: int | None = None
    skipped_invalid_count: int = 0


@dataclass(frozen=True)
class DownloadResult:
    status: DownloadStatus = DownloadStatus.DOWNLOADED
    output_path: Path | None = None
    quality_notes: tuple[str, ...] = ()
    skipped_invalid_count: int = 0


@dataclass(frozen=True)
class QualityReport:
    url: str
    lang: str
    resolved_lang: str
    title: str | None
    uploader: str | None
    available_langs: tuple[str, ...]
    video_qualities: tuple[str, ...]
    audio_qualities: tuple[str, ...]
    skipped_invalid_count: int = 0


def ydl_base_opts() -> YdlParams:
    """Options needed for YouTube multi-language audio extraction."""
    return {
        "extractor_args": {
            "youtube": {
                "player_client": ["all"],
            },
        },
        "js_runtimes": {
            "node": cast(dict[str, str], {}),
        },
    }


def get_video_info(
    url: str,
    verbose: bool = False,
    debug: bool = False,
    retry_on_network_failure: int = DEFAULT_RETRY_ON_NETWORK_FAILURE,
) -> InfoDict:
    """Fetch video metadata without downloading the video."""
    try:
        with yt_dlp.YoutubeDL(
            {
                **ydl_base_opts(),
                **_network_retry_ydl_opts(retry_on_network_failure),
                **_yt_dlp_output_opts(verbose=verbose, debug=debug),
            }
        ) as ydl:
            info = ydl.extract_info(url, download=False)
    except YoutubeDLError as exc:
        raise errors.MetadataExtractionError(
            f"Could not extract video metadata: {exc}"
        ) from exc
    if not isinstance(info, dict):
        raise errors.MetadataExtractionError(
            "Could not extract video metadata: "
            f"unexpected metadata shape ({type(info).__name__})"
        )
    return info


def get_available_audio_langs(info: InfoDict) -> set[str]:
    """Return the set of available audio languages for this video."""
    return set(collect_audio_language_inventory(info).langs)


def collect_audio_language_inventory(
    info: InfoDict,
) -> languages.AudioLanguageInventory:
    """Return validated audio language metadata for this video."""
    return languages.collect_available_audio_langs(info)


def get_audio_language_inventory_for_url(
    url: str,
    verbose: bool = False,
    debug: bool = False,
    retry_on_network_failure: int = DEFAULT_RETRY_ON_NETWORK_FAILURE,
) -> languages.AudioLanguageInventory:
    """Fetch video metadata and return validated audio language inventory."""
    return collect_audio_language_inventory(
        get_video_info(
            url,
            verbose=verbose,
            debug=debug,
            retry_on_network_failure=retry_on_network_failure,
        )
    )


def get_available_audio_langs_for_url(
    url: str,
    verbose: bool = False,
    debug: bool = False,
    retry_on_network_failure: int = DEFAULT_RETRY_ON_NETWORK_FAILURE,
) -> set[str]:
    """Fetch video metadata and return available audio languages."""
    return get_available_audio_langs(
        get_video_info(
            url,
            verbose=verbose,
            debug=debug,
            retry_on_network_failure=retry_on_network_failure,
        )
    )


def _resolve_video_language(
    info: InfoDict,
    canonical_lang: str,
) -> tuple[languages.AudioLanguageInventory, str]:
    inventory = collect_audio_language_inventory(info)
    resolved_lang = languages.resolve_language_for_video(
        canonical_lang,
        inventory,
        title=_optional_string(info.get("title")),
    )
    return inventory, resolved_lang


def get_quality_report(
    url: str,
    lang: str,
    verbose: bool = False,
    debug: bool = False,
    retry_on_network_failure: int = DEFAULT_RETRY_ON_NETWORK_FAILURE,
) -> QualityReport:
    """Fetch metadata and return available quality choices for a URL."""
    info = get_video_info(
        url,
        verbose=verbose,
        debug=debug,
        retry_on_network_failure=retry_on_network_failure,
    )
    inventory, resolved_lang = _resolve_video_language(info, lang)
    audio_candidates = quality.get_audio_quality_candidates(info, resolved_lang)
    return QualityReport(
        url=url,
        lang=lang,
        resolved_lang=resolved_lang,
        title=_optional_string(info.get("title")),
        uploader=_optional_string(info.get("uploader")),
        available_langs=languages.display_language_tags(inventory.langs),
        video_qualities=quality.format_video_quality_labels(
            quality.get_available_video_heights(info)
        ),
        audio_qualities=quality.format_audio_quality_labels(audio_candidates),
        skipped_invalid_count=inventory.skipped_invalid_count,
    )


def ensure_lang(info: InfoDict, target: str) -> str:
    """Raise an error if the requested dub language is not available."""
    _, resolved_lang = _resolve_video_language(info, target)
    return resolved_lang


def outtmpl(lang: str, output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> str:
    """Output template: <output_dir>/<lang>/<uploader>/<title>/<title>.<ext>"""
    return str(
        Path(output_dir) / lang / "%(uploader)s" / "%(title)s" / "%(title)s.%(ext)s"
    )


def plan_download(
    url: str,
    lang: str,
    download_mode: DownloadMode | str = DownloadMode.VIDEO,
    ffmpeg_path: str | Path | None = None,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    merge_output_format: str = DEFAULT_MERGE_OUTPUT_FORMAT,
    video_quality: quality.VideoQuality | str = quality.DEFAULT_VIDEO_QUALITY,
    audio_quality: quality.AudioQuality | str = quality.DEFAULT_AUDIO_QUALITY,
    verbose: bool = False,
    debug: bool = False,
    retry_on_network_failure: int = DEFAULT_RETRY_ON_NETWORK_FAILURE,
    exists_behavior: FileExistsBehavior | str = DEFAULT_EXISTS_BEHAVIOR,
) -> DownloadPlan:
    """Validate and describe a download without writing files."""
    selected_download_mode = normalize_download_mode(download_mode)
    selected_exists_behavior = normalize_exists_behavior(exists_behavior)
    info = get_video_info(
        url,
        verbose=verbose,
        debug=debug,
        retry_on_network_failure=retry_on_network_failure,
    )
    inventory, resolved_lang = _resolve_video_language(info, lang)
    quality_selection = quality.resolve_quality_selection(
        info=info,
        lang=resolved_lang,
        download_mode=selected_download_mode,
        video_quality=video_quality,
        audio_quality=audio_quality,
    )
    selected_info: list[InfoDict] = []
    output_path = _planned_output_path(
        info=info,
        lang=resolved_lang,
        download_mode=selected_download_mode,
        ffmpeg_path=ffmpeg_path,
        output_dir=output_dir,
        merge_output_format=merge_output_format,
        format_selector=quality_selection.format_selector,
        verbose=verbose,
        debug=debug,
        retry_on_network_failure=retry_on_network_failure,
        selected_info_callback=selected_info.append,
    )
    output_exists = _output_path_exists(output_path)

    return DownloadPlan(
        url=url,
        lang=lang,
        resolved_lang=resolved_lang,
        download_mode=selected_download_mode,
        video_quality=(
            quality_selection.video_quality.label
            if quality_selection.video_quality
            else None
        ),
        selected_video_quality=quality_selection.selected_video_label,
        audio_quality=quality_selection.audio_quality.label,
        selected_audio_quality=quality_selection.selected_audio_label,
        quality_notes=quality_selection.notes,
        title=_optional_string(info.get("title")),
        uploader=_optional_string(info.get("uploader")),
        available_langs=languages.display_language_tags(inventory.langs),
        output_path=output_path,
        exists_behavior=selected_exists_behavior,
        output_exists=output_exists,
        estimated_size_bytes=_estimated_download_size_bytes(
            selected_info[0] if selected_info else None
        ),
        skipped_invalid_count=inventory.skipped_invalid_count,
    )


def download(
    url: str,
    lang: str,
    download_mode: DownloadMode | str = DownloadMode.VIDEO,
    ffmpeg_path: str | Path | None = None,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    merge_output_format: str = DEFAULT_MERGE_OUTPUT_FORMAT,
    video_quality: quality.VideoQuality | str = quality.DEFAULT_VIDEO_QUALITY,
    audio_quality: quality.AudioQuality | str = quality.DEFAULT_AUDIO_QUALITY,
    verbose: bool = False,
    debug: bool = False,
    retry_on_network_failure: int = DEFAULT_RETRY_ON_NETWORK_FAILURE,
    exists_behavior: FileExistsBehavior | str = DEFAULT_EXISTS_BEHAVIOR,
    stage_callback: DownloadStageCallback | None = None,
    progress_callback: DownloadProgressCallback | None = None,
    approval_callback: DownloadApprovalCallback | None = None,
) -> DownloadResult:
    """Download a single URL with the specified dub language and mode."""
    selected_download_mode = normalize_download_mode(download_mode)
    selected_exists_behavior = normalize_exists_behavior(exists_behavior)
    _report_download_stage(stage_callback, DownloadStage.FETCHING_METADATA)
    info = get_video_info(
        url,
        verbose=verbose,
        debug=debug,
        retry_on_network_failure=retry_on_network_failure,
    )
    _report_download_stage(stage_callback, DownloadStage.CHECKING_LANGUAGES)
    inventory, resolved_lang = _resolve_video_language(info, lang)
    _report_download_stage(stage_callback, DownloadStage.SELECTING_QUALITIES)
    quality_selection = quality.resolve_quality_selection(
        info=info,
        lang=resolved_lang,
        download_mode=selected_download_mode,
        video_quality=video_quality,
        audio_quality=audio_quality,
    )
    _report_download_stage(stage_callback, DownloadStage.PLANNING_OUTPUT)
    selected_info: list[InfoDict] = []
    output_path = _planned_output_path(
        info=info,
        lang=resolved_lang,
        download_mode=selected_download_mode,
        ffmpeg_path=ffmpeg_path,
        output_dir=output_dir,
        merge_output_format=merge_output_format,
        format_selector=quality_selection.format_selector,
        verbose=verbose,
        debug=debug,
        retry_on_network_failure=retry_on_network_failure,
        selected_info_callback=selected_info.append,
    )
    download_plan = DownloadPlan(
        url=url,
        lang=lang,
        resolved_lang=resolved_lang,
        download_mode=selected_download_mode,
        video_quality=(
            quality_selection.video_quality.label
            if quality_selection.video_quality
            else None
        ),
        selected_video_quality=quality_selection.selected_video_label,
        audio_quality=quality_selection.audio_quality.label,
        selected_audio_quality=quality_selection.selected_audio_label,
        quality_notes=quality_selection.notes,
        title=_optional_string(info.get("title")),
        uploader=_optional_string(info.get("uploader")),
        available_langs=languages.display_language_tags(inventory.langs),
        output_path=output_path,
        exists_behavior=selected_exists_behavior,
        output_exists=_output_path_exists(output_path),
        estimated_size_bytes=_estimated_download_size_bytes(
            selected_info[0] if selected_info else None
        ),
        skipped_invalid_count=inventory.skipped_invalid_count,
    )
    if _handle_existing_output(output_path, selected_exists_behavior):
        _report_download_stage(
            stage_callback,
            DownloadStage.SKIPPING_EXISTING_OUTPUT,
        )
        return DownloadResult(
            status=DownloadStatus.SKIPPED,
            output_path=output_path,
            quality_notes=quality_selection.notes,
            skipped_invalid_count=inventory.skipped_invalid_count,
        )
    if approval_callback is not None and not approval_callback(download_plan):
        return DownloadResult(
            status=DownloadStatus.CANCELLED,
            output_path=output_path,
            quality_notes=quality_selection.notes,
            skipped_invalid_count=inventory.skipped_invalid_count,
        )
    if _handle_existing_output(output_path, selected_exists_behavior):
        _report_download_stage(
            stage_callback,
            DownloadStage.SKIPPING_EXISTING_OUTPUT,
        )
        return DownloadResult(
            status=DownloadStatus.SKIPPED,
            output_path=output_path,
            quality_notes=quality_selection.notes,
            skipped_invalid_count=inventory.skipped_invalid_count,
        )

    _report_download_stage(stage_callback, DownloadStage.PREPARING_OUTPUT_DIR)

    try:
        _cleanup_stale_incomplete_downloads(output_dir)
        with (
            _download_signal_handlers(),
            _DownloadStagingRun(output_dir) as staging_run,
        ):
            staged_output_path = _staged_output_path(
                output_path,
                output_dir=output_dir,
                staging_output_dir=staging_run.output_dir,
            )
            _report_download_stage(stage_callback, DownloadStage.DOWNLOADING_MEDIA)
            try:
                with yt_dlp.YoutubeDL(
                    _download_ydl_opts(
                        lang=resolved_lang,
                        download_mode=selected_download_mode,
                        ffmpeg_path=ffmpeg_path,
                        output_dir=staging_run.output_dir,
                        merge_output_format=merge_output_format,
                        format_selector=quality_selection.format_selector,
                        verbose=verbose,
                        debug=debug,
                        retry_on_network_failure=retry_on_network_failure,
                        exists_behavior=selected_exists_behavior,
                        stage_callback=stage_callback,
                        progress_callback=progress_callback,
                    )
                ) as ydl:
                    ydl.download([url])
            except YoutubeDLError as exc:
                raise errors.DownloadError(f"Could not download media: {exc}") from exc
            _report_download_stage(stage_callback, DownloadStage.FINALIZING_OUTPUT)
            final_status = _finalize_staged_download(
                staged_output_path=staged_output_path,
                final_output_path=output_path,
                output_dir=output_dir,
                staging_output_dir=staging_run.output_dir,
                exists_behavior=selected_exists_behavior,
            )
    except _UnsafeStagingPathError as exc:
        raise errors.DownloadError(str(exc)) from exc
    except OSError as exc:
        raise errors.DownloadError(
            f"Could not prepare output directory: {exc}"
        ) from exc
    if final_status == DownloadStatus.SKIPPED:
        _report_download_stage(
            stage_callback,
            DownloadStage.SKIPPING_EXISTING_OUTPUT,
        )
        return DownloadResult(
            status=DownloadStatus.SKIPPED,
            output_path=output_path,
            quality_notes=quality_selection.notes,
            skipped_invalid_count=inventory.skipped_invalid_count,
        )
    return DownloadResult(
        status=DownloadStatus.DOWNLOADED,
        output_path=output_path,
        quality_notes=quality_selection.notes,
        skipped_invalid_count=inventory.skipped_invalid_count,
    )


def _download_ydl_opts(
    *,
    lang: str,
    download_mode: DownloadMode | str,
    ffmpeg_path: str | Path | None,
    output_dir: str | Path,
    merge_output_format: str,
    format_selector: str,
    verbose: bool,
    debug: bool,
    retry_on_network_failure: int,
    exists_behavior: FileExistsBehavior | str | None = None,
    stage_callback: DownloadStageCallback | None = None,
    progress_callback: DownloadProgressCallback | None = None,
) -> YdlParams:
    selected_download_mode = normalize_download_mode(download_mode)
    ydl_opts: YdlParams = {
        **ydl_base_opts(),
        **_network_retry_ydl_opts(retry_on_network_failure),
        **_yt_dlp_output_opts(verbose=verbose, debug=debug),
        "format": format_selector,
        "outtmpl": outtmpl(lang, output_dir),
        "restrictfilenames": True,
        "continuedl": False,
        "nopart": False,
    }
    if selected_download_mode == DownloadMode.VIDEO:
        ydl_opts["merge_output_format"] = merge_output_format
    if exists_behavior is not None:
        selected_exists_behavior = normalize_exists_behavior(exists_behavior)
        ydl_opts["overwrites"] = (
            selected_exists_behavior == FileExistsBehavior.OVERWRITE
        )
    if ffmpeg_path:
        ydl_opts["ffmpeg_location"] = str(ffmpeg_path)
    if stage_callback is not None or progress_callback is not None:
        ydl_opts["progress_hooks"] = [
            _make_progress_hook(stage_callback, progress_callback)
        ]
        if stage_callback is not None:
            ydl_opts["postprocessor_hooks"] = [
                _make_postprocessor_hook(stage_callback, selected_download_mode)
            ]
    return ydl_opts


def _parse_download_progress(progress: Mapping[str, Any]) -> DownloadProgress | None:
    if progress.get("status") != "downloading":
        return None

    downloaded_bytes = progress.get("downloaded_bytes")
    total_bytes = progress.get("total_bytes") or progress.get("total_bytes_estimate")
    percent: float | None = None
    if downloaded_bytes is not None and total_bytes:
        percent = min(100.0, max(0.0, downloaded_bytes / total_bytes * 100))

    speed = progress.get("speed")
    eta = progress.get("eta")
    return DownloadProgress(
        speed_bytes_per_sec=float(speed) if speed is not None else None,
        eta_seconds=int(eta) if eta is not None else None,
        percent=percent,
    )


def _make_progress_hook(
    stage_callback: DownloadStageCallback | None,
    progress_callback: DownloadProgressCallback | None = None,
) -> Callable[[Mapping[str, Any]], None]:
    def progress_hook(progress: Mapping[str, Any]) -> None:
        if progress.get("status") != "downloading":
            return
        if stage_callback is not None:
            stage_callback(DownloadStage.DOWNLOADING_MEDIA)
        if progress_callback is not None:
            parsed = _parse_download_progress(progress)
            if parsed is not None:
                progress_callback(parsed)

    return progress_hook


def _make_postprocessor_hook(
    stage_callback: DownloadStageCallback,
    download_mode: DownloadMode,
) -> Callable[[Mapping[str, Any]], None]:
    def postprocessor_hook(progress: Mapping[str, Any]) -> None:
        if download_mode == DownloadMode.VIDEO and progress.get("status") in {
            "started",
            "processing",
        }:
            stage_callback(DownloadStage.MERGING_MEDIA)

    return postprocessor_hook


def _report_download_stage(
    stage_callback: DownloadStageCallback | None,
    stage: DownloadStage,
) -> None:
    if stage_callback is not None:
        stage_callback(stage)


class _StagingLock:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._file: Any | None = None

    def acquire(self, *, blocking: bool) -> bool:
        lock_file = self._path.open("a+b")
        try:
            if os.name == "nt":
                self._acquire_windows(lock_file, blocking=blocking)
            else:
                self._acquire_posix(lock_file, blocking=blocking)
        except OSError:
            lock_file.close()
            if blocking:
                raise
            return False
        self._file = lock_file
        return True

    def release(self) -> None:
        if self._file is None:
            return
        try:
            if os.name == "nt":
                self._release_windows(self._file)
            else:
                self._release_posix(self._file)
        finally:
            self._file.close()
            self._file = None

    @staticmethod
    def _acquire_posix(lock_file: Any, *, blocking: bool) -> None:
        import fcntl

        flags = fcntl.LOCK_EX
        if not blocking:
            flags |= fcntl.LOCK_NB
        fcntl.flock(lock_file.fileno(), flags)

    @staticmethod
    def _release_posix(lock_file: Any) -> None:
        import fcntl

        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def _acquire_windows(lock_file: Any, *, blocking: bool) -> None:
        import importlib

        msvcrt = cast(_MsvcrtModule, importlib.import_module("msvcrt"))

        lock_file.seek(0)
        lock_file.write(b"\0")
        lock_file.flush()
        lock_file.seek(0)
        mode = msvcrt.LK_LOCK if blocking else msvcrt.LK_NBLCK
        msvcrt.locking(lock_file.fileno(), mode, 1)

    @staticmethod
    def _release_windows(lock_file: Any) -> None:
        import importlib

        msvcrt = cast(_MsvcrtModule, importlib.import_module("msvcrt"))

        lock_file.seek(0)
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)


class _DownloadStagingRun:
    def __init__(self, output_dir: str | Path) -> None:
        self._output_dir = Path(output_dir)
        self._creation_lock = _StagingLock(
            _incomplete_downloads_dir(output_dir) / INCOMPLETE_CLEANUP_LOCK_FILENAME
        )
        self.output_dir = _new_staging_output_dir(output_dir)
        self._lock = _StagingLock(self.output_dir / RUN_LOCK_FILENAME)

    def __enter__(self) -> _DownloadStagingRun:
        try:
            _ensure_safe_incomplete_downloads_dir(self._output_dir)
            self._creation_lock.acquire(blocking=True)
            _ensure_safe_incomplete_downloads_dir(self._output_dir)
            self.output_dir.mkdir(exist_ok=False)
            _ensure_safe_incomplete_downloads_path(self._output_dir)
            _raise_if_redirected_staging_path(self.output_dir)
            self._lock.acquire(blocking=True)
            _write_staging_metadata(self.output_dir)
        except BaseException:
            self._lock.release()
            _remove_staging_output_dir(self.output_dir)
            raise
        finally:
            self._creation_lock.release()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self._lock.release()
        _remove_staging_output_dir(self.output_dir)


def _incomplete_downloads_dir(output_dir: str | Path) -> Path:
    return Path(output_dir) / INCOMPLETE_DOWNLOAD_DIR


def _staging_component_dirs(output_dir: str | Path) -> tuple[Path, Path]:
    output_dir_path = Path(output_dir)
    tmp_dir = output_dir_path / INCOMPLETE_DOWNLOAD_DIR.parts[0]
    return tmp_dir, _incomplete_downloads_dir(output_dir_path)


def _is_redirected_staging_path(path: Path) -> bool:
    try:
        if stat.S_ISLNK(path.lstat().st_mode):
            return True
    except FileNotFoundError:
        return False

    is_junction = getattr(path, "is_junction", None)
    try:
        if is_junction is not None and is_junction():
            return True
    except NotImplementedError:
        pass

    is_mount = getattr(path, "is_mount", None)
    try:
        return is_mount is not None and is_mount()
    except NotImplementedError:
        return False


def _raise_if_redirected_staging_path(path: Path) -> None:
    if _is_redirected_staging_path(path):
        raise _UnsafeStagingPathError(
            f"Refusing to use symlinked or redirected staging directory: {path}"
        )


def _ensure_safe_incomplete_downloads_path(output_dir: str | Path) -> Path:
    for component_dir in _staging_component_dirs(output_dir):
        _raise_if_redirected_staging_path(component_dir)
    return _incomplete_downloads_dir(output_dir)


def _ensure_safe_incomplete_downloads_dir(output_dir: str | Path) -> Path:
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    for component_dir in _staging_component_dirs(output_dir_path):
        _raise_if_redirected_staging_path(component_dir)
        try:
            component_dir.mkdir()
        except FileExistsError:
            _raise_if_redirected_staging_path(component_dir)
            if not component_dir.is_dir():
                raise NotADirectoryError(
                    f"Staging path is not a directory: {component_dir}"
                ) from None
        _raise_if_redirected_staging_path(component_dir)

    return _incomplete_downloads_dir(output_dir_path)


def _new_staging_output_dir(output_dir: str | Path) -> Path:
    run_id = f"{time.time_ns()}-{os.getpid()}-{uuid.uuid4().hex[:8]}"
    return _incomplete_downloads_dir(output_dir) / run_id


def _write_staging_metadata(
    staging_output_dir: Path,
    *,
    finalizing_copy_dirs: tuple[Path, ...] = (),
) -> None:
    metadata = {
        "application": RUN_METADATA_APPLICATION,
        "metadata_version": RUN_METADATA_VERSION,
        "pid": os.getpid(),
        "created_at": time.time(),
    }
    if finalizing_copy_dirs:
        metadata[RUN_METADATA_FINALIZING_COPY_DIRS] = [
            str(path) for path in finalizing_copy_dirs
        ]
    _write_staging_metadata_file(staging_output_dir, metadata)


def _write_staging_metadata_file(
    staging_output_dir: Path,
    metadata: dict[str, Any],
) -> None:
    metadata_path = staging_output_dir / RUN_METADATA_FILENAME
    metadata_tmp_path = metadata_path.with_name(
        f".{metadata_path.name}.{uuid.uuid4().hex}.tmp"
    )
    try:
        with metadata_tmp_path.open("w", encoding="utf-8") as metadata_file:
            json.dump(metadata, metadata_file, sort_keys=True)
            _fsync_file(metadata_file)
        metadata_tmp_path.replace(metadata_path)
        _fsync_parent_dir(metadata_path)
    except BaseException:
        with contextlib.suppress(FileNotFoundError, OSError):
            metadata_tmp_path.unlink()
        raise


def _load_owned_staging_metadata(staging_output_dir: Path) -> dict[str, Any] | None:
    metadata_path = staging_output_dir / RUN_METADATA_FILENAME
    try:
        if _is_redirected_staging_path(staging_output_dir):
            return None
        metadata_stat = metadata_path.lstat()
        if not stat.S_ISREG(metadata_stat.st_mode):
            return None
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None

    if (
        isinstance(metadata, dict)
        and metadata.get("application") == RUN_METADATA_APPLICATION
        and metadata.get("metadata_version") == RUN_METADATA_VERSION
    ):
        return metadata
    return None


def _is_owned_staging_output_dir(staging_output_dir: Path) -> bool:
    return _load_owned_staging_metadata(staging_output_dir) is not None


def _record_finalizing_copy_dir(
    *,
    staging_output_dir: Path,
    finalizing_copy_dir: Path,
    output_dir: str | Path,
) -> None:
    metadata = _load_owned_staging_metadata(staging_output_dir)
    if metadata is None:
        raise OSError(f"Staging metadata is missing or invalid: {staging_output_dir}")

    raw_dirs = metadata.get(RUN_METADATA_FINALIZING_COPY_DIRS, [])
    if isinstance(raw_dirs, list):
        finalizing_copy_dirs = [path for path in raw_dirs if isinstance(path, str)]
    else:
        finalizing_copy_dirs = []

    relative_finalizing_copy_dir = _output_relative_path(
        finalizing_copy_dir,
        output_dir=output_dir,
    )
    if not _is_valid_finalizing_copy_dir(relative_finalizing_copy_dir):
        raise OSError(f"Invalid finalizing copy directory: {finalizing_copy_dir}")

    finalizing_copy_dir_text = str(relative_finalizing_copy_dir)
    if finalizing_copy_dir_text not in finalizing_copy_dirs:
        finalizing_copy_dirs.append(finalizing_copy_dir_text)
    metadata[RUN_METADATA_FINALIZING_COPY_DIRS] = finalizing_copy_dirs
    _write_staging_metadata_file(staging_output_dir, metadata)


def _output_relative_path(path: Path, *, output_dir: str | Path) -> Path:
    output_dir_path = Path(output_dir)
    try:
        return path.relative_to(output_dir_path)
    except ValueError:
        try:
            return path.resolve(strict=False).relative_to(
                output_dir_path.resolve(strict=False)
            )
        except ValueError as exc:
            raise OSError(f"Path is outside output directory: {path}") from exc


def _is_valid_finalizing_copy_dir(path: Path) -> bool:
    if path.is_absolute() or path.drive or path.root:
        return False
    parts = path.parts
    return (
        bool(parts)
        and parts[-1] == FINALIZING_COPY_DIR_NAME
        and all(part not in ("", ".", "..") for part in parts)
    )


def _finalizing_copy_path(
    *,
    staging_output_dir: Path,
    final_output_path: Path,
) -> Path:
    path = _finalizing_copy_dir(final_output_path) / f"{staging_output_dir.name}.tmp"
    if path.is_absolute():
        return path
    return path.absolute()


def _finalizing_copy_dir(final_output_path: Path) -> Path:
    return final_output_path.parent / FINALIZING_COPY_DIR_NAME


def _is_owned_finalizing_copy_dir_stat(
    finalizing_copy_dir_stat: os.stat_result,
) -> bool:
    if not stat.S_ISDIR(finalizing_copy_dir_stat.st_mode):
        return False
    if os.name != "posix":
        return True
    return finalizing_copy_dir_stat.st_uid == os.getuid()


def _has_unsafe_finalizing_copy_dir_mode(
    finalizing_copy_dir_stat: os.stat_result,
) -> bool:
    return bool(
        os.name == "posix"
        and finalizing_copy_dir_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
    )


def _is_safe_finalizing_copy_dir_stat(finalizing_copy_dir_stat: os.stat_result) -> bool:
    if not _is_owned_finalizing_copy_dir_stat(finalizing_copy_dir_stat):
        return False
    return not _has_unsafe_finalizing_copy_dir_mode(finalizing_copy_dir_stat)


def _is_safe_finalizing_copy_file_stat(
    finalizing_copy_stat: os.stat_result,
) -> bool:
    if not stat.S_ISREG(finalizing_copy_stat.st_mode):
        return False
    return not (os.name == "posix" and finalizing_copy_stat.st_uid != os.getuid())


def _ensure_safe_finalizing_copy_dir(finalizing_copy_dir: Path) -> None:
    finalizing_copy_dir_stat = finalizing_copy_dir.lstat()
    if not _is_safe_finalizing_copy_dir_stat(finalizing_copy_dir_stat):
        raise OSError(f"Unsafe finalizing copy directory: {finalizing_copy_dir}")


def _tighten_finalizing_copy_dir_permissions(finalizing_copy_dir: Path) -> None:
    if os.name != "posix":
        return
    finalizing_copy_dir_stat = finalizing_copy_dir.lstat()
    if (
        stat.S_ISDIR(finalizing_copy_dir_stat.st_mode)
        and finalizing_copy_dir_stat.st_uid == os.getuid()
        and _has_unsafe_finalizing_copy_dir_mode(finalizing_copy_dir_stat)
    ):
        finalizing_copy_dir.chmod(FINALIZING_COPY_DIR_MODE)


def _ensure_finalizing_copy_dir(final_output_path: Path) -> Path:
    finalizing_copy_dir = _finalizing_copy_dir(final_output_path)
    finalizing_copy_dir.mkdir(
        mode=FINALIZING_COPY_DIR_MODE,
        parents=True,
        exist_ok=True,
    )
    _tighten_finalizing_copy_dir_permissions(finalizing_copy_dir)
    _ensure_safe_finalizing_copy_dir(finalizing_copy_dir)
    return finalizing_copy_dir


def _remove_empty_finalizing_copy_dir(finalizing_copy_path: Path) -> None:
    finalizing_copy_dir = finalizing_copy_path.parent
    with contextlib.suppress(OSError):
        _ensure_safe_finalizing_copy_dir(finalizing_copy_dir)
        finalizing_copy_dir.rmdir()


def _cleanup_finalizing_copy_by_path(
    finalizing_copy_dir: Path,
    expected_name: str,
) -> bool:
    try:
        finalizing_copy_dir_stat = finalizing_copy_dir.lstat()
    except FileNotFoundError:
        return True
    except OSError:
        return False
    if not _is_owned_finalizing_copy_dir_stat(finalizing_copy_dir_stat):
        return True
    if _has_unsafe_finalizing_copy_dir_mode(finalizing_copy_dir_stat):
        try:
            finalizing_copy_dir.chmod(FINALIZING_COPY_DIR_MODE)
            finalizing_copy_dir_stat = finalizing_copy_dir.lstat()
        except OSError:
            return False
    if not _is_safe_finalizing_copy_dir_stat(finalizing_copy_dir_stat):
        return False

    finalizing_copy_path = finalizing_copy_dir / expected_name
    try:
        finalizing_copy_stat = finalizing_copy_path.lstat()
    except FileNotFoundError:
        return True
    except OSError:
        return False
    if not _is_safe_finalizing_copy_file_stat(finalizing_copy_stat):
        return True

    try:
        finalizing_copy_path.unlink()
        _remove_empty_finalizing_copy_dir(finalizing_copy_path)
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return True


def _cleanup_finalizing_copy_with_dir_fd(
    finalizing_copy_dir: Path,
    expected_name: str,
) -> bool:
    try:
        finalizing_copy_dir_stat = finalizing_copy_dir.lstat()
    except FileNotFoundError:
        return True
    except OSError:
        return False
    if not _is_owned_finalizing_copy_dir_stat(finalizing_copy_dir_stat):
        return True

    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW

    dir_fd = None
    try:
        dir_fd = os.open(finalizing_copy_dir, flags)
        opened_dir_stat = os.fstat(dir_fd)
        if (
            opened_dir_stat.st_dev != finalizing_copy_dir_stat.st_dev
            or opened_dir_stat.st_ino != finalizing_copy_dir_stat.st_ino
            or not _is_owned_finalizing_copy_dir_stat(opened_dir_stat)
        ):
            return False
        if _has_unsafe_finalizing_copy_dir_mode(opened_dir_stat):
            os.fchmod(dir_fd, FINALIZING_COPY_DIR_MODE)
            opened_dir_stat = os.fstat(dir_fd)
            if not _is_safe_finalizing_copy_dir_stat(opened_dir_stat):
                return False
        try:
            finalizing_copy_stat = os.stat(
                expected_name,
                dir_fd=dir_fd,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            return True
        except OSError:
            return False
        if not _is_safe_finalizing_copy_file_stat(finalizing_copy_stat):
            return True
        try:
            os.unlink(expected_name, dir_fd=dir_fd)
        except FileNotFoundError:
            return True
        except OSError:
            return False
    except OSError:
        return False
    finally:
        if dir_fd is not None:
            with contextlib.suppress(OSError):
                os.close(dir_fd)

    _remove_empty_finalizing_copy_dir(finalizing_copy_dir / expected_name)
    return True


def _cleanup_finalizing_copy(
    finalizing_copy_dir: Path,
    expected_name: str,
) -> bool:
    if _CLEANUP_FINALIZING_COPY_SUPPORTS_DIR_FD:
        return _cleanup_finalizing_copy_with_dir_fd(
            finalizing_copy_dir,
            expected_name,
        )
    return _cleanup_finalizing_copy_by_path(finalizing_copy_dir, expected_name)


def _cleanup_stale_incomplete_downloads(output_dir: str | Path) -> None:
    incomplete_dir = _ensure_safe_incomplete_downloads_path(output_dir)
    if not incomplete_dir.exists():
        return
    cleanup_lock = _StagingLock(incomplete_dir / INCOMPLETE_CLEANUP_LOCK_FILENAME)
    try:
        if not cleanup_lock.acquire(blocking=False):
            return
        _ensure_safe_incomplete_downloads_path(output_dir)
        children = tuple(incomplete_dir.iterdir())
        _ensure_safe_incomplete_downloads_path(output_dir)
    except _UnsafeStagingPathError:
        raise
    except OSError:
        return
    finally:
        cleanup_lock.release()

    for child in children:
        try:
            _ensure_safe_incomplete_downloads_path(output_dir)
            if _is_redirected_staging_path(child) or not child.is_dir():
                continue
            metadata = _load_owned_staging_metadata(child)
            if metadata is None:
                continue
        except _UnsafeStagingPathError:
            raise
        except OSError:
            continue
        lock = _StagingLock(child / RUN_LOCK_FILENAME)
        try:
            acquired = lock.acquire(blocking=False)
        except OSError:
            continue
        if not acquired:
            continue
        try:
            metadata = _load_owned_staging_metadata(child)
            if metadata is not None and _cleanup_stale_finalizing_copies(
                output_dir,
                child,
                metadata,
            ):
                lock.release()
                _remove_staging_output_dir(child)
        finally:
            lock.release()


def _cleanup_stale_finalizing_copies(
    output_dir: str | Path,
    staging_output_dir: Path,
    metadata: dict[str, Any],
) -> bool:
    raw_dirs = metadata.get(RUN_METADATA_FINALIZING_COPY_DIRS, [])
    if not isinstance(raw_dirs, list):
        return True

    expected_name = f"{staging_output_dir.name}.tmp"
    clean = True
    for raw_dir in raw_dirs:
        if not isinstance(raw_dir, str):
            continue
        relative_finalizing_copy_dir = Path(raw_dir)
        if not _is_valid_finalizing_copy_dir(relative_finalizing_copy_dir):
            continue
        finalizing_copy_dir = Path(output_dir) / relative_finalizing_copy_dir
        if not _cleanup_finalizing_copy(finalizing_copy_dir, expected_name):
            clean = False
    return clean


def _remove_staging_output_dir(staging_output_dir: Path) -> None:
    try:
        should_skip = (
            _is_redirected_staging_path(staging_output_dir.parent.parent)
            or _is_redirected_staging_path(staging_output_dir.parent)
            or _is_redirected_staging_path(staging_output_dir)
        )
    except OSError:
        return
    if should_skip:
        return
    with contextlib.suppress(FileNotFoundError, OSError):
        shutil.rmtree(staging_output_dir)


def _staged_output_path(
    final_output_path: Path,
    *,
    output_dir: str | Path,
    staging_output_dir: Path,
) -> Path:
    final_path = Path(final_output_path)
    output_dir_path = Path(output_dir)
    try:
        relative_output_path = final_path.relative_to(output_dir_path)
    except ValueError:
        try:
            relative_output_path = final_path.resolve(strict=False).relative_to(
                output_dir_path.resolve(strict=False)
            )
        except ValueError as exc:
            raise errors.DownloadError(
                f"Planned output path is outside output directory: {final_path}"
            ) from exc
    return staging_output_dir / relative_output_path


def _is_cross_device_error(exc: OSError) -> bool:
    return (
        exc.errno == errno.EXDEV
        or getattr(exc, "winerror", None) == WINDOWS_ERROR_NOT_SAME_DEVICE
    )


def _copy_staged_download_to_finalizing_path(
    *,
    staged_output_path: Path,
    final_output_path: Path,
    staging_output_dir: Path,
    output_dir: str | Path,
) -> Path:
    final_output_path.parent.mkdir(parents=True, exist_ok=True)
    finalizing_copy_dir = _ensure_finalizing_copy_dir(final_output_path)
    finalizing_copy_path = _finalizing_copy_path(
        staging_output_dir=staging_output_dir,
        final_output_path=final_output_path,
    )
    _record_finalizing_copy_dir(
        staging_output_dir=staging_output_dir,
        finalizing_copy_dir=finalizing_copy_dir,
        output_dir=output_dir,
    )
    created_finalizing_copy = False
    try:
        with finalizing_copy_path.open("xb") as destination:
            created_finalizing_copy = True
            with staged_output_path.open("rb") as source:
                shutil.copyfileobj(
                    source,
                    destination,
                    length=FINALIZE_COPY_BUFFER_SIZE,
                )
            with contextlib.suppress(OSError):
                staged_mode = stat.S_IMODE(staged_output_path.stat().st_mode)
                os.chmod(finalizing_copy_path, staged_mode)
            _fsync_file(destination)
    except BaseException:
        if created_finalizing_copy:
            with contextlib.suppress(FileNotFoundError, OSError):
                finalizing_copy_path.unlink()
            _remove_empty_finalizing_copy_dir(finalizing_copy_path)
        raise

    return finalizing_copy_path


def _fsync_file(file_obj: Any) -> None:
    file_obj.flush()
    os.fsync(file_obj.fileno())


def _fsync_parent_dir(path: Path) -> None:
    if os.name == "nt":
        return

    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY

    with contextlib.suppress(OSError):
        dir_fd = os.open(path.parent, flags)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)


def _publish_file_no_clobber(source_path: Path, destination_path: Path) -> None:
    if sys.platform.startswith("linux"):
        _publish_file_no_clobber_linux(source_path, destination_path)
        return
    if sys.platform == "darwin":
        _publish_file_no_clobber_darwin(source_path, destination_path)
        return
    if os.name == "nt":
        _publish_file_no_clobber_windows(source_path, destination_path)
        return

    raise _AtomicNoClobberPublishUnsupportedError(
        "Atomic no-clobber publish is not supported on this platform"
    )


def _publish_file_no_clobber_linux(source_path: Path, destination_path: Path) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    source_bytes = os.fsencode(source_path)
    destination_bytes = os.fsencode(destination_path)

    try:
        renameat2 = libc.renameat2
    except AttributeError:
        _publish_file_no_clobber_linux_syscall(
            libc,
            source_bytes,
            destination_bytes,
            destination_path,
        )
        return

    renameat2.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    renameat2.restype = ctypes.c_int
    ctypes.set_errno(0)
    result = renameat2(
        AT_FDCWD,
        source_bytes,
        AT_FDCWD,
        destination_bytes,
        LINUX_RENAME_NOREPLACE,
    )
    if result != 0:
        _raise_posix_no_clobber_publish_error(ctypes.get_errno(), destination_path)


def _publish_file_no_clobber_linux_syscall(
    libc: Any,
    source_bytes: bytes,
    destination_bytes: bytes,
    destination_path: Path,
) -> None:
    syscall_number = LINUX_RENAMEAT2_SYSCALL_NUMBERS.get(platform.machine().lower())
    if syscall_number is None:
        raise _AtomicNoClobberPublishUnsupportedError(
            "renameat2 syscall number is unknown for this architecture"
        )

    try:
        syscall = libc.syscall
    except AttributeError as exc:
        raise _AtomicNoClobberPublishUnsupportedError(
            "libc syscall entry point is unavailable"
        ) from exc

    syscall.restype = ctypes.c_long
    ctypes.set_errno(0)
    result = syscall(
        ctypes.c_long(syscall_number),
        ctypes.c_int(AT_FDCWD),
        ctypes.c_char_p(source_bytes),
        ctypes.c_int(AT_FDCWD),
        ctypes.c_char_p(destination_bytes),
        ctypes.c_uint(LINUX_RENAME_NOREPLACE),
    )
    if result != 0:
        _raise_posix_no_clobber_publish_error(ctypes.get_errno(), destination_path)


def _publish_file_no_clobber_darwin(source_path: Path, destination_path: Path) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    try:
        renamex_np = libc.renamex_np
    except AttributeError as exc:
        raise _AtomicNoClobberPublishUnsupportedError(
            "renamex_np is unavailable on this platform"
        ) from exc

    renamex_np.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
    renamex_np.restype = ctypes.c_int
    ctypes.set_errno(0)
    result = renamex_np(
        os.fsencode(source_path),
        os.fsencode(destination_path),
        DARWIN_RENAME_EXCL,
    )
    if result != 0:
        _raise_posix_no_clobber_publish_error(ctypes.get_errno(), destination_path)


def _publish_file_no_clobber_windows(
    source_path: Path,
    destination_path: Path,
) -> None:
    from ctypes import wintypes

    win_ctypes = cast(_WindowsCtypesModule, ctypes)
    kernel32 = win_ctypes.WinDLL("kernel32", use_last_error=True)
    move_file_ex = kernel32.MoveFileExW
    move_file_ex.argtypes = [
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.DWORD,
    ]
    move_file_ex.restype = wintypes.BOOL

    win_ctypes.set_last_error(0)
    result = move_file_ex(
        str(source_path),
        str(destination_path),
        WINDOWS_MOVEFILE_WRITE_THROUGH,
    )
    if result:
        return

    error_code = win_ctypes.get_last_error()
    _raise_windows_no_clobber_publish_error(error_code, destination_path)


def _raise_posix_no_clobber_publish_error(
    error_code: int,
    destination_path: Path,
) -> None:
    if error_code == errno.EEXIST:
        raise FileExistsError(
            error_code,
            os.strerror(error_code),
            str(destination_path),
        )

    unsupported_errors = {
        errno.ENOSYS,
        errno.EINVAL,
        errno.EXDEV,
    }
    for name in ("EOPNOTSUPP", "ENOTSUP"):
        if (value := getattr(errno, name, None)) is not None:
            unsupported_errors.add(value)

    if error_code in unsupported_errors:
        raise _AtomicNoClobberPublishUnsupportedError(
            error_code,
            os.strerror(error_code),
            str(destination_path),
        )

    raise OSError(error_code, os.strerror(error_code), str(destination_path))


def _raise_windows_no_clobber_publish_error(
    error_code: int,
    destination_path: Path,
) -> None:
    message = _windows_error_message(error_code)
    if error_code in (WINDOWS_ERROR_FILE_EXISTS, WINDOWS_ERROR_ALREADY_EXISTS):
        raise FileExistsError(
            error_code,
            message,
            str(destination_path),
        )

    if error_code in (
        WINDOWS_ERROR_NOT_SAME_DEVICE,
        WINDOWS_ERROR_CALL_NOT_IMPLEMENTED,
    ):
        raise _AtomicNoClobberPublishUnsupportedError(
            error_code,
            message,
            str(destination_path),
        )

    raise OSError(error_code, message, str(destination_path))


def _windows_error_message(error_code: int) -> str:
    format_error = getattr(ctypes, "FormatError", None)
    if format_error is None:
        return f"Windows error {error_code}"
    return str(format_error(error_code))


def _finalize_staged_download(
    *,
    staged_output_path: Path,
    final_output_path: Path,
    output_dir: str | Path,
    staging_output_dir: Path,
    exists_behavior: FileExistsBehavior,
) -> DownloadStatus:
    if not staged_output_path.is_file():
        raise errors.DownloadError(
            f"Completed staged download is missing: {staged_output_path}"
        )

    if _handle_existing_output(final_output_path, exists_behavior):
        return DownloadStatus.SKIPPED

    try:
        final_output_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise errors.DownloadError(
            f"Could not prepare output directory: {exc}"
        ) from exc

    if exists_behavior != FileExistsBehavior.OVERWRITE:
        return _finalize_staged_download_without_overwriting(
            staged_output_path=staged_output_path,
            final_output_path=final_output_path,
            output_dir=output_dir,
            staging_output_dir=staging_output_dir,
            exists_behavior=exists_behavior,
        )

    try:
        staged_output_path.replace(final_output_path)
    except OSError as exc:
        if _is_cross_device_error(exc):
            return _copy_staged_download_with_overwrite(
                staged_output_path=staged_output_path,
                final_output_path=final_output_path,
                output_dir=output_dir,
                staging_output_dir=staging_output_dir,
                replace_error=exc,
            )
        raise errors.DownloadError(f"Could not finalize output: {exc}") from exc
    _fsync_parent_dir(final_output_path)
    return DownloadStatus.DOWNLOADED


def _copy_staged_download_with_overwrite(
    *,
    staged_output_path: Path,
    final_output_path: Path,
    output_dir: str | Path,
    staging_output_dir: Path,
    replace_error: OSError,
) -> DownloadStatus:
    try:
        finalizing_copy_path = _copy_staged_download_to_finalizing_path(
            staged_output_path=staged_output_path,
            final_output_path=final_output_path,
            output_dir=output_dir,
            staging_output_dir=staging_output_dir,
        )
    except OSError as exc:
        raise errors.DownloadError(
            f"Could not finalize output after replace failed ({replace_error}): {exc}"
        ) from exc

    try:
        finalizing_copy_path.replace(final_output_path)
    except OSError as exc:
        with contextlib.suppress(FileNotFoundError, OSError):
            finalizing_copy_path.unlink()
        _remove_empty_finalizing_copy_dir(finalizing_copy_path)
        raise errors.DownloadError(
            f"Could not finalize output after replace failed ({replace_error}): {exc}"
        ) from exc
    except BaseException:
        with contextlib.suppress(FileNotFoundError, OSError):
            finalizing_copy_path.unlink()
        _remove_empty_finalizing_copy_dir(finalizing_copy_path)
        raise

    _fsync_parent_dir(final_output_path)
    _remove_empty_finalizing_copy_dir(finalizing_copy_path)
    with contextlib.suppress(FileNotFoundError, OSError):
        staged_output_path.unlink()
    return DownloadStatus.DOWNLOADED


def _finalize_staged_download_without_overwriting(
    *,
    staged_output_path: Path,
    final_output_path: Path,
    output_dir: str | Path,
    staging_output_dir: Path,
    exists_behavior: FileExistsBehavior,
) -> DownloadStatus:
    try:
        os.link(staged_output_path, final_output_path)
    except FileExistsError as exc:
        if _handle_existing_output(final_output_path, exists_behavior):
            return DownloadStatus.SKIPPED
        raise errors.DownloadError(f"Could not finalize output: {exc}") from exc
    except OSError as exc:
        return _copy_staged_download_without_overwriting(
            staged_output_path=staged_output_path,
            final_output_path=final_output_path,
            output_dir=output_dir,
            staging_output_dir=staging_output_dir,
            exists_behavior=exists_behavior,
            hard_link_error=exc,
        )

    with contextlib.suppress(FileNotFoundError, OSError):
        staged_output_path.unlink()
    _fsync_parent_dir(final_output_path)
    return DownloadStatus.DOWNLOADED


def _copy_staged_download_without_overwriting(
    *,
    staged_output_path: Path,
    final_output_path: Path,
    output_dir: str | Path,
    staging_output_dir: Path,
    exists_behavior: FileExistsBehavior,
    hard_link_error: OSError,
) -> DownloadStatus:
    if _handle_existing_output(final_output_path, exists_behavior):
        return DownloadStatus.SKIPPED

    try:
        finalizing_copy_path = _copy_staged_download_to_finalizing_path(
            staged_output_path=staged_output_path,
            final_output_path=final_output_path,
            output_dir=output_dir,
            staging_output_dir=staging_output_dir,
        )
    except OSError as exc:
        raise errors.DownloadError(
            f"Could not finalize output after hard link failed ({hard_link_error}): {exc}"
        ) from exc

    try:
        _publish_file_no_clobber(finalizing_copy_path, final_output_path)
    except FileExistsError as exc:
        with contextlib.suppress(FileNotFoundError, OSError):
            finalizing_copy_path.unlink()
        _remove_empty_finalizing_copy_dir(finalizing_copy_path)
        if _handle_existing_output(final_output_path, exists_behavior):
            return DownloadStatus.SKIPPED
        raise errors.DownloadError(f"Could not finalize output: {exc}") from exc
    except _AtomicNoClobberPublishUnsupportedError as exc:
        with contextlib.suppress(FileNotFoundError, OSError):
            finalizing_copy_path.unlink()
        _remove_empty_finalizing_copy_dir(finalizing_copy_path)
        raise errors.DownloadError(
            "Could not finalize output after hard link failed "
            f"({hard_link_error}): atomic no-clobber publish is unavailable: {exc}"
        ) from exc
    except OSError as exc:
        with contextlib.suppress(FileNotFoundError, OSError):
            finalizing_copy_path.unlink()
        _remove_empty_finalizing_copy_dir(finalizing_copy_path)
        raise errors.DownloadError(
            f"Could not finalize output after hard link failed ({hard_link_error}): {exc}"
        ) from exc
    except BaseException:
        with contextlib.suppress(FileNotFoundError, OSError):
            finalizing_copy_path.unlink()
        _remove_empty_finalizing_copy_dir(finalizing_copy_path)
        raise

    _fsync_parent_dir(final_output_path)
    _remove_empty_finalizing_copy_dir(finalizing_copy_path)
    with contextlib.suppress(FileNotFoundError, OSError):
        staged_output_path.unlink()
    return DownloadStatus.DOWNLOADED


@contextlib.contextmanager
def _download_signal_handlers() -> Any:
    handled_signals = tuple(
        signum
        for name in ("SIGTERM", "SIGHUP")
        if (signum := getattr(signal, name, None)) is not None
    )
    previous_handlers: dict[int, Any] = {}

    def handle_signal(signum: int, frame: Any) -> None:
        raise SystemExit(128 + signum)

    try:
        for signum in handled_signals:
            previous_handlers[signum] = signal.getsignal(signum)
            signal.signal(signum, handle_signal)
    except ValueError:
        previous_handlers.clear()
    try:
        yield
    finally:
        for signum, previous_handler in previous_handlers.items():
            signal.signal(signum, previous_handler)


def _planned_output_path(
    *,
    info: InfoDict,
    lang: str,
    download_mode: DownloadMode | str,
    ffmpeg_path: str | Path | None,
    output_dir: str | Path,
    merge_output_format: str,
    format_selector: str,
    verbose: bool,
    debug: bool,
    retry_on_network_failure: int,
    selected_info_callback: Callable[[InfoDict], None] | None = None,
) -> Path:
    planned_info = _copy_info_for_planning(info)
    ydl_opts = _download_ydl_opts(
        lang=lang,
        download_mode=download_mode,
        ffmpeg_path=ffmpeg_path,
        output_dir=output_dir,
        merge_output_format=merge_output_format,
        format_selector=format_selector,
        verbose=verbose,
        debug=debug,
        retry_on_network_failure=retry_on_network_failure,
    )

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            selected_info = ydl.process_ie_result(planned_info, download=False)
            if selected_info_callback is not None and isinstance(selected_info, dict):
                selected_info_callback(selected_info)
            filename = ydl.prepare_filename(selected_info)
    except YoutubeDLError as exc:
        raise errors.DownloadError(f"Could not plan download output: {exc}") from exc

    if not filename:
        raise errors.DownloadError("Could not determine planned output path.")
    return Path(filename)


def _estimated_download_size_bytes(
    selected_info: InfoDict | None,
) -> int | None:
    if selected_info is None:
        return None

    requested_formats = selected_info.get("requested_formats")
    if isinstance(requested_formats, list) and requested_formats:
        return _requested_formats_size_bytes(requested_formats)

    return _format_size_bytes(selected_info)


def _requested_formats_size_bytes(formats: list[Any]) -> int | None:
    total = 0
    for format_info in formats:
        if not isinstance(format_info, dict):
            return None
        format_size = _format_size_bytes(format_info)
        if format_size is None:
            return None
        total += format_size
    return total or None


def _format_size_bytes(format_info: Mapping[str, Any]) -> int | None:
    return _positive_size_bytes(format_info.get("filesize")) or _positive_size_bytes(
        format_info.get("filesize_approx")
    )


def _positive_size_bytes(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value > 0:
        return value
    if isinstance(value, float) and value > 0:
        return int(value)
    return None


def _output_path_exists(output_path: Path) -> bool:
    if output_path.exists():
        if not output_path.is_file():
            raise errors.DownloadError(
                f"Output path already exists but is not a file: {output_path}"
            )
        return True
    if output_path.is_symlink():
        raise errors.DownloadError(
            f"Output path already exists but is not a file: {output_path}"
        )
    return False


def _handle_existing_output(
    output_path: Path,
    exists_behavior: FileExistsBehavior,
) -> bool:
    output_exists = _output_path_exists(output_path)
    if not output_exists:
        return False

    if exists_behavior == FileExistsBehavior.SKIP:
        return True
    if exists_behavior == FileExistsBehavior.FAIL:
        raise errors.DownloadError(f"Output already exists: {output_path}")
    return False


def _copy_info_for_planning(info: InfoDict) -> InfoDict:
    planned_info = dict(info)
    formats = info.get("formats")
    if isinstance(formats, list):
        planned_info["formats"] = [
            dict(format_info) if isinstance(format_info, dict) else format_info
            for format_info in formats
        ]
    return cast(InfoDict, planned_info)


def _optional_string(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _yt_dlp_output_opts(
    *,
    verbose: bool,
    debug: bool,
) -> YdlParams:
    if debug:
        return {
            "quiet": False,
            "no_warnings": False,
            "verbose": True,
        }
    if verbose:
        return {
            "quiet": False,
            "no_warnings": False,
            "verbose": False,
        }
    return {
        "quiet": True,
        "no_warnings": True,
        "verbose": False,
        "noprogress": True,
    }


def _network_retry_ydl_opts(retry_on_network_failure: int) -> YdlParams:
    retry_count = _validate_retry_on_network_failure(retry_on_network_failure)
    return cast(
        YdlParams,
        {
            "retries": retry_count,
            "fragment_retries": retry_count,
            "extractor_retries": retry_count,
            "retry_sleep_functions": {
                "http": _retry_sleep_seconds,
                "fragment": _retry_sleep_seconds,
                "extractor": _retry_sleep_seconds,
            },
        },
    )


def _validate_retry_on_network_failure(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("retry_on_network_failure must be a non-negative integer.")
    if value < 0:
        raise ValueError("retry_on_network_failure must be a non-negative integer.")
    return value


def _retry_sleep_seconds(n: int) -> float:
    base_delay = min(2**n, MAX_RETRY_SLEEP_SECONDS)
    return float(base_delay + random.random())
