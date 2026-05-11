from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yt_dlp

DEFAULT_OUTPUT_DIR = Path("Videos")
DEFAULT_MERGE_OUTPUT_FORMAT = "mkv"


@dataclass(frozen=True)
class DownloadPlan:
    url: str
    lang: str
    title: str | None
    uploader: str | None
    available_langs: tuple[str, ...]
    output_path: Path


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
    quiet: bool = True,
    verbose: bool = False,
) -> dict[str, Any]:
    """Fetch video metadata without downloading the video."""
    with yt_dlp.YoutubeDL(
        {
            **ydl_base_opts(),
            **_yt_dlp_diagnostic_opts(quiet=quiet, verbose=verbose),
        }
    ) as ydl:
        info = ydl.extract_info(url, download=False)
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


def get_available_audio_langs_for_url(url: str, verbose: bool = False) -> set[str]:
    """Fetch video metadata and return available audio languages."""
    return get_available_audio_langs(get_video_info(url, verbose=verbose))


def ensure_lang(info: dict[str, Any], target: str) -> None:
    """Raise an error if the requested dub language is not available."""
    langs = get_available_audio_langs(info)
    if target not in langs:
        title = info.get("title")
        if not langs:
            raise RuntimeError(f"No multi-language audio tracks found for '{title}'.")
        raise RuntimeError(
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
    ffmpeg_path: str | Path | None = None,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    merge_output_format: str = DEFAULT_MERGE_OUTPUT_FORMAT,
    verbose: bool = False,
) -> DownloadPlan:
    """Validate and describe a download without writing files."""
    info = get_video_info(url, verbose=verbose)
    ensure_lang(info, lang)

    return DownloadPlan(
        url=url,
        lang=lang,
        title=_optional_string(info.get("title")),
        uploader=_optional_string(info.get("uploader")),
        available_langs=tuple(sorted(get_available_audio_langs(info))),
        output_path=_planned_output_path(
            info=info,
            lang=lang,
            ffmpeg_path=ffmpeg_path,
            output_dir=output_dir,
            merge_output_format=merge_output_format,
        ),
    )


def download(
    url: str,
    lang: str,
    ffmpeg_path: str | Path | None = None,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    merge_output_format: str = DEFAULT_MERGE_OUTPUT_FORMAT,
    verbose: bool = False,
) -> None:
    """Download a single video with the specified dub language."""
    info = get_video_info(url, verbose=verbose)
    ensure_lang(info, lang)

    Path(output_dir, lang).mkdir(parents=True, exist_ok=True)
    with yt_dlp.YoutubeDL(
        _download_ydl_opts(
            lang=lang,
            ffmpeg_path=ffmpeg_path,
            output_dir=output_dir,
            merge_output_format=merge_output_format,
            verbose=verbose,
        )
    ) as ydl:
        ydl.download([url])


def _download_ydl_opts(
    *,
    lang: str,
    ffmpeg_path: str | Path | None,
    output_dir: str | Path,
    merge_output_format: str,
    verbose: bool,
) -> dict[str, Any]:
    ydl_opts: dict[str, Any] = {
        **ydl_base_opts(),
        **_yt_dlp_diagnostic_opts(verbose=verbose),
        "format": f"bv*+bestaudio[language=\"{lang}\"]",
        "outtmpl": outtmpl(lang, output_dir),
        "restrictfilenames": True,
        "merge_output_format": merge_output_format,
    }
    if ffmpeg_path:
        ydl_opts["ffmpeg_location"] = str(ffmpeg_path)
    return ydl_opts


def _planned_output_path(
    *,
    info: dict[str, Any],
    lang: str,
    ffmpeg_path: str | Path | None,
    output_dir: str | Path,
    merge_output_format: str,
) -> Path:
    planned_info = {**info, "ext": merge_output_format}
    ydl_opts = _download_ydl_opts(
        lang=lang,
        ffmpeg_path=ffmpeg_path,
        output_dir=output_dir,
        merge_output_format=merge_output_format,
        verbose=False,
    )

    with yt_dlp.YoutubeDL({**ydl_opts, "quiet": True}) as ydl:
        filename = ydl.prepare_filename(planned_info)

    if not filename:
        raise RuntimeError("Could not determine planned output path.")
    return Path(filename)


def _optional_string(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _yt_dlp_diagnostic_opts(
    *,
    verbose: bool,
    quiet: bool | None = None,
) -> dict[str, Any]:
    opts: dict[str, Any] = {
        "verbose": verbose,
        "no_warnings": not verbose,
    }
    if quiet is not None:
        opts["quiet"] = False if verbose else quiet
    return opts
