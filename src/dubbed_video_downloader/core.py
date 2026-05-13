from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yt_dlp
from yt_dlp.utils import YoutubeDLError

from . import errors
from . import quality
from .download_mode import DownloadMode
from .download_mode import normalize_download_mode

DEFAULT_OUTPUT_DIR = Path("Videos")
DEFAULT_MERGE_OUTPUT_FORMAT = "mkv"
DEFAULT_RETRY_ON_NETWORK_FAILURE = 3
MAX_RETRY_SLEEP_SECONDS = 8.0


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


@dataclass(frozen=True)
class DownloadResult:
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
            raise errors.LanguageUnavailableError(
                f"No multi-language audio tracks found for '{title}'."
            )
        raise errors.LanguageUnavailableError(
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
) -> DownloadPlan:
    """Validate and describe a download without writing files."""
    selected_download_mode = normalize_download_mode(download_mode)
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
        output_path=_planned_output_path(
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
        ),
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
) -> DownloadResult:
    """Download a single URL with the specified dub language and mode."""
    selected_download_mode = normalize_download_mode(download_mode)
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

    Path(output_dir, lang).mkdir(parents=True, exist_ok=True)
    with yt_dlp.YoutubeDL(
        _download_ydl_opts(
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
    ) as ydl:
        ydl.download([url])
    return DownloadResult(quality_notes=quality_selection.notes)


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
) -> dict[str, Any]:
    selected_download_mode = normalize_download_mode(download_mode)
    ydl_opts: dict[str, Any] = {
        **ydl_base_opts(),
        **_network_retry_ydl_opts(retry_on_network_failure),
        **_yt_dlp_output_opts(verbose=verbose, debug=debug),
        "format": format_selector,
        "outtmpl": outtmpl(lang, output_dir),
        "restrictfilenames": True,
    }
    if selected_download_mode == DownloadMode.VIDEO:
        ydl_opts["merge_output_format"] = merge_output_format
    if ffmpeg_path:
        ydl_opts["ffmpeg_location"] = str(ffmpeg_path)
    return ydl_opts


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

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        selected_info = ydl.process_ie_result(planned_info, download=False)
        filename = ydl.prepare_filename(selected_info)

    if not filename:
        raise RuntimeError("Could not determine planned output path.")
    return Path(filename)


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
