from __future__ import annotations

import contextlib
import json
import os
import random
import shutil
import signal
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yt_dlp
from yt_dlp.utils import YoutubeDLError

from . import errors
from . import quality
from .download_mode import DownloadMode
from .download_mode import normalize_download_mode
from .exists_behavior import FileExistsBehavior
from .exists_behavior import normalize_exists_behavior

DEFAULT_OUTPUT_DIR = Path("Videos")
DEFAULT_MERGE_OUTPUT_FORMAT = "mkv"
DEFAULT_RETRY_ON_NETWORK_FAILURE = 3
DEFAULT_EXISTS_BEHAVIOR = FileExistsBehavior.SKIP
MAX_RETRY_SLEEP_SECONDS = 8.0
INCOMPLETE_DOWNLOAD_DIR = Path("tmp") / ".incomplete"
INCOMPLETE_CLEANUP_LOCK_FILENAME = ".cleanup.lock"
RUN_LOCK_FILENAME = ".lock"
RUN_METADATA_FILENAME = "run.json"


class DownloadStatus(str, Enum):
    DOWNLOADED = "downloaded"
    SKIPPED = "skipped"


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


@dataclass(frozen=True)
class DownloadPlan:
    url: str
    lang: str
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


@dataclass(frozen=True)
class DownloadResult:
    status: DownloadStatus = DownloadStatus.DOWNLOADED
    output_path: Path | None = None
    quality_notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class QualityReport:
    url: str
    lang: str
    title: str | None
    uploader: str | None
    available_langs: tuple[str, ...]
    video_qualities: tuple[str, ...]
    audio_qualities: tuple[str, ...]


def ydl_base_opts() -> dict[str, Any]:
    """Options needed for YouTube multi-language audio extraction."""
    return {
        "extractor_args": {
            "youtube": {
                "player_client": ["all"],
            },
        },
        "js_runtimes": {
            "node": {},
        },
    }


def get_video_info(
    url: str,
    verbose: bool = False,
    debug: bool = False,
    retry_on_network_failure: int = DEFAULT_RETRY_ON_NETWORK_FAILURE,
) -> dict[str, Any]:
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
    return info


def get_available_audio_langs(info: dict[str, Any]) -> set[str]:
    """Return the set of available audio languages for this video."""
    langs = set()
    for format_info in info.get("formats", []):
        if format_info.get("vcodec") == "none" and format_info.get("acodec") not in (
            None,
            "none",
        ):
            if format_info.get("language"):
                langs.add(format_info["language"])
    return langs


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
    ensure_lang(info, lang)
    audio_candidates = quality.get_audio_quality_candidates(info, lang)
    return QualityReport(
        url=url,
        lang=lang,
        title=_optional_string(info.get("title")),
        uploader=_optional_string(info.get("uploader")),
        available_langs=tuple(sorted(get_available_audio_langs(info))),
        video_qualities=quality.format_video_quality_labels(
            quality.get_available_video_heights(info)
        ),
        audio_qualities=quality.format_audio_quality_labels(audio_candidates),
    )


def ensure_lang(info: dict[str, Any], target: str) -> None:
    """Raise an error if the requested dub language is not available."""
    langs = get_available_audio_langs(info)
    if target not in langs:
        title = info.get("title")
        if not langs:
            raise errors.LanguageNotFoundError(
                f"No multi-language audio tracks found for '{title}'."
            )
        raise errors.LanguageNotFoundError(
            f"Requested dub language not found for '{title}'.\n"
            f"Requested: {target}\n"
            f"Available: {', '.join(sorted(langs))}"
        )


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
    ensure_lang(info, lang)
    quality_selection = quality.resolve_quality_selection(
        info=info,
        lang=lang,
        download_mode=selected_download_mode,
        video_quality=video_quality,
        audio_quality=audio_quality,
    )
    output_path = _planned_output_path(
        info=info,
        lang=lang,
        download_mode=selected_download_mode,
        ffmpeg_path=ffmpeg_path,
        output_dir=output_dir,
        merge_output_format=merge_output_format,
        format_selector=quality_selection.format_selector,
        verbose=verbose,
        debug=debug,
        retry_on_network_failure=retry_on_network_failure,
    )
    output_exists = _output_path_exists(output_path)

    return DownloadPlan(
        url=url,
        lang=lang,
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
        available_langs=tuple(sorted(get_available_audio_langs(info))),
        output_path=output_path,
        exists_behavior=selected_exists_behavior,
        output_exists=output_exists,
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
    ensure_lang(info, lang)
    _report_download_stage(stage_callback, DownloadStage.SELECTING_QUALITIES)
    quality_selection = quality.resolve_quality_selection(
        info=info,
        lang=lang,
        download_mode=selected_download_mode,
        video_quality=video_quality,
        audio_quality=audio_quality,
    )
    _report_download_stage(stage_callback, DownloadStage.PLANNING_OUTPUT)
    output_path = _planned_output_path(
        info=info,
        lang=lang,
        download_mode=selected_download_mode,
        ffmpeg_path=ffmpeg_path,
        output_dir=output_dir,
        merge_output_format=merge_output_format,
        format_selector=quality_selection.format_selector,
        verbose=verbose,
        debug=debug,
        retry_on_network_failure=retry_on_network_failure,
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
        )

    _report_download_stage(stage_callback, DownloadStage.PREPARING_OUTPUT_DIR)
    _cleanup_stale_incomplete_downloads(output_dir)

    try:
        with _download_signal_handlers():
            with _DownloadStagingRun(output_dir) as staging_run:
                staged_output_path = _staged_output_path(
                    output_path,
                    output_dir=output_dir,
                    staging_output_dir=staging_run.output_dir,
                )
                _report_download_stage(stage_callback, DownloadStage.DOWNLOADING_MEDIA)
                try:
                    with yt_dlp.YoutubeDL(
                        _download_ydl_opts(
                            lang=lang,
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
                        )
                    ) as ydl:
                        ydl.download([url])
                except YoutubeDLError as exc:
                    raise errors.DownloadError(
                        f"Could not download media: {exc}"
                    ) from exc
                _report_download_stage(stage_callback, DownloadStage.FINALIZING_OUTPUT)
                final_status = _finalize_staged_download(
                    staged_output_path=staged_output_path,
                    final_output_path=output_path,
                    exists_behavior=selected_exists_behavior,
                )
    except OSError as exc:
        raise errors.DownloadError(f"Could not prepare output directory: {exc}") from exc
    if final_status == DownloadStatus.SKIPPED:
        _report_download_stage(
            stage_callback,
            DownloadStage.SKIPPING_EXISTING_OUTPUT,
        )
        return DownloadResult(
            status=DownloadStatus.SKIPPED,
            output_path=output_path,
            quality_notes=quality_selection.notes,
        )
    return DownloadResult(
        status=DownloadStatus.DOWNLOADED,
        output_path=output_path,
        quality_notes=quality_selection.notes,
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
) -> dict[str, Any]:
    selected_download_mode = normalize_download_mode(download_mode)
    ydl_opts: dict[str, Any] = {
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
    if stage_callback is not None:
        ydl_opts["progress_hooks"] = [_make_progress_hook(stage_callback)]
        ydl_opts["postprocessor_hooks"] = [
            _make_postprocessor_hook(stage_callback, selected_download_mode)
        ]
    return ydl_opts


def _make_progress_hook(
    stage_callback: DownloadStageCallback,
) -> Callable[[dict[str, Any]], None]:
    def progress_hook(progress: dict[str, Any]) -> None:
        if progress.get("status") == "downloading":
            stage_callback(DownloadStage.DOWNLOADING_MEDIA)

    return progress_hook


def _make_postprocessor_hook(
    stage_callback: DownloadStageCallback,
    download_mode: DownloadMode,
) -> Callable[[dict[str, Any]], None]:
    def postprocessor_hook(progress: dict[str, Any]) -> None:
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
        self._path.parent.mkdir(parents=True, exist_ok=True)
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
        import msvcrt

        lock_file.seek(0)
        lock_file.write(b"\0")
        lock_file.flush()
        lock_file.seek(0)
        mode = msvcrt.LK_LOCK if blocking else msvcrt.LK_NBLCK
        msvcrt.locking(lock_file.fileno(), mode, 1)

    @staticmethod
    def _release_windows(lock_file: Any) -> None:
        import msvcrt

        lock_file.seek(0)
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)


class _DownloadStagingRun:
    def __init__(self, output_dir: str | Path) -> None:
        self._creation_lock = _StagingLock(
            _incomplete_downloads_dir(output_dir) / INCOMPLETE_CLEANUP_LOCK_FILENAME
        )
        self.output_dir = _new_staging_output_dir(output_dir)
        self._lock = _StagingLock(self.output_dir / RUN_LOCK_FILENAME)

    def __enter__(self) -> _DownloadStagingRun:
        try:
            self._creation_lock.acquire(blocking=True)
            self.output_dir.mkdir(parents=True, exist_ok=False)
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


def _new_staging_output_dir(output_dir: str | Path) -> Path:
    run_id = f"{time.time_ns()}-{os.getpid()}-{uuid.uuid4().hex[:8]}"
    return _incomplete_downloads_dir(output_dir) / run_id


def _write_staging_metadata(staging_output_dir: Path) -> None:
    metadata = {
        "pid": os.getpid(),
        "created_at": time.time(),
    }
    metadata_path = staging_output_dir / RUN_METADATA_FILENAME
    metadata_path.write_text(json.dumps(metadata, sort_keys=True), encoding="utf-8")


def _cleanup_stale_incomplete_downloads(output_dir: str | Path) -> None:
    incomplete_dir = _incomplete_downloads_dir(output_dir)
    if not incomplete_dir.exists():
        return
    cleanup_lock = _StagingLock(incomplete_dir / INCOMPLETE_CLEANUP_LOCK_FILENAME)
    try:
        if not cleanup_lock.acquire(blocking=False):
            return
        children = tuple(incomplete_dir.iterdir())
    except OSError:
        return
    finally:
        cleanup_lock.release()

    for child in children:
        if child.is_symlink() or not child.is_dir():
            continue
        lock = _StagingLock(child / RUN_LOCK_FILENAME)
        try:
            acquired = lock.acquire(blocking=False)
        except OSError:
            continue
        if not acquired:
            continue
        try:
            lock.release()
            _remove_staging_output_dir(child)
        finally:
            lock.release()


def _remove_staging_output_dir(staging_output_dir: Path) -> None:
    if staging_output_dir.is_symlink():
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


def _finalize_staged_download(
    *,
    staged_output_path: Path,
    final_output_path: Path,
    exists_behavior: FileExistsBehavior,
) -> DownloadStatus:
    if not staged_output_path.is_file():
        raise errors.DownloadError(
            f"Completed staged download is missing: {staged_output_path}"
        )

    if _output_path_exists(final_output_path):
        if exists_behavior == FileExistsBehavior.SKIP:
            return DownloadStatus.SKIPPED
        if exists_behavior == FileExistsBehavior.FAIL:
            raise errors.DownloadError(f"Output already exists: {final_output_path}")

    try:
        final_output_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise errors.DownloadError(f"Could not prepare output directory: {exc}") from exc

    try:
        staged_output_path.replace(final_output_path)
    except OSError as exc:
        raise errors.DownloadError(f"Could not finalize output: {exc}") from exc
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
    info: dict[str, Any],
    lang: str,
    download_mode: DownloadMode | str,
    ffmpeg_path: str | Path | None,
    output_dir: str | Path,
    merge_output_format: str,
    format_selector: str,
    verbose: bool,
    debug: bool,
    retry_on_network_failure: int,
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
            filename = ydl.prepare_filename(selected_info)
    except YoutubeDLError as exc:
        raise errors.DownloadError(f"Could not plan download output: {exc}") from exc

    if not filename:
        raise errors.DownloadError("Could not determine planned output path.")
    return Path(filename)


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


def _copy_info_for_planning(info: dict[str, Any]) -> dict[str, Any]:
    planned_info = dict(info)
    formats = info.get("formats")
    if isinstance(formats, list):
        planned_info["formats"] = [
            dict(format_info) if isinstance(format_info, dict) else format_info
            for format_info in formats
        ]
    return planned_info


def _optional_string(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _yt_dlp_output_opts(
    *,
    verbose: bool,
    debug: bool,
) -> dict[str, Any]:
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
    }


def _network_retry_ydl_opts(retry_on_network_failure: int) -> dict[str, Any]:
    retry_count = _validate_retry_on_network_failure(retry_on_network_failure)
    return {
        "retries": retry_count,
        "fragment_retries": retry_count,
        "extractor_retries": retry_count,
        "retry_sleep_functions": {
            "http": _retry_sleep_seconds,
            "fragment": _retry_sleep_seconds,
            "extractor": _retry_sleep_seconds,
        },
    }


def _validate_retry_on_network_failure(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("retry_on_network_failure must be a non-negative integer.")
    if value < 0:
        raise ValueError("retry_on_network_failure must be a non-negative integer.")
    return value


def _retry_sleep_seconds(attempt: int) -> float:
    base_delay = min(2**attempt, MAX_RETRY_SLEEP_SECONDS)
    return base_delay + random.random()
