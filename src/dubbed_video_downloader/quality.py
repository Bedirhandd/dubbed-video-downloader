from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .download_mode import DownloadMode
from .download_mode import normalize_download_mode
from .errors import QualityError

MIN_VIDEO_HEIGHT = 144
MAX_VIDEO_HEIGHT = 8640
MEDIUM_VIDEO_TARGET_HEIGHT = 720
MEDIUM_AUDIO_TARGET_KBPS = 128.0


class VideoQualityKind(str, Enum):
    BEST = "best"
    MEDIUM = "medium"
    LOW = "low"
    EXACT = "exact"


class AudioQualityKind(str, Enum):
    BEST = "best"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class VideoQuality:
    kind: VideoQualityKind
    height: int | None = None

    def __post_init__(self) -> None:
        if self.kind == VideoQualityKind.EXACT:
            if self.height is None:
                raise ValueError("exact video quality requires a height")
            if self.height < MIN_VIDEO_HEIGHT or self.height > MAX_VIDEO_HEIGHT:
                raise ValueError(
                    f"video height must be between {MIN_VIDEO_HEIGHT}p and "
                    f"{MAX_VIDEO_HEIGHT}p"
                )
            return

        if self.height is not None:
            raise ValueError("preset video quality must not include a height")

    @property
    def label(self) -> str:
        if self.kind == VideoQualityKind.EXACT:
            return f"{self.height}p"
        return self.kind.value

    def __str__(self) -> str:
        return self.label


@dataclass(frozen=True)
class AudioQuality:
    kind: AudioQualityKind

    @property
    def label(self) -> str:
        return self.kind.value

    def __str__(self) -> str:
        return self.label


@dataclass(frozen=True)
class AudioQualityCandidate:
    format_id: str | None
    bitrate_kbps: float | None
    bitrate_field: str | None
    ext: str | None
    acodec: str | None


@dataclass(frozen=True)
class QualitySelection:
    video_quality: VideoQuality | None
    audio_quality: AudioQuality
    format_selector: str
    selected_video_label: str | None
    selected_audio_label: str
    notes: tuple[str, ...] = ()


DEFAULT_VIDEO_QUALITY = VideoQuality(VideoQualityKind.BEST)
DEFAULT_AUDIO_QUALITY = AudioQuality(AudioQualityKind.BEST)

_EXACT_VIDEO_QUALITY_RE = re.compile(r"([1-9][0-9]*)p")
_VIDEO_PRESETS = {
    VideoQualityKind.BEST.value: DEFAULT_VIDEO_QUALITY,
    VideoQualityKind.MEDIUM.value: VideoQuality(VideoQualityKind.MEDIUM),
    VideoQualityKind.LOW.value: VideoQuality(VideoQualityKind.LOW),
}
_AUDIO_PRESETS = {
    AudioQualityKind.BEST.value: DEFAULT_AUDIO_QUALITY,
    AudioQualityKind.MEDIUM.value: AudioQuality(AudioQualityKind.MEDIUM),
    AudioQualityKind.LOW.value: AudioQuality(AudioQualityKind.LOW),
}


def normalize_video_quality(
    value: Any,
    *,
    key: str = "video_quality",
) -> VideoQuality:
    if isinstance(value, VideoQuality):
        return value
    if not isinstance(value, str):
        raise QualityError(_video_quality_error(key))

    text = value.strip().lower()
    if text in _VIDEO_PRESETS:
        return _VIDEO_PRESETS[text]

    match = _EXACT_VIDEO_QUALITY_RE.fullmatch(text)
    if not match:
        raise QualityError(_video_quality_error(key))

    height = int(match.group(1))
    if height < MIN_VIDEO_HEIGHT or height > MAX_VIDEO_HEIGHT:
        raise QualityError(
            f"{key} must be between {MIN_VIDEO_HEIGHT}p and {MAX_VIDEO_HEIGHT}p."
        )
    return VideoQuality(VideoQualityKind.EXACT, height)


def normalize_audio_quality(
    value: Any,
    *,
    key: str = "audio_quality",
) -> AudioQuality:
    if isinstance(value, AudioQuality):
        return value
    if not isinstance(value, str):
        raise QualityError(_audio_quality_error(key))

    text = value.strip().lower()
    if text not in _AUDIO_PRESETS:
        raise QualityError(_audio_quality_error(key))
    return _AUDIO_PRESETS[text]


def resolve_quality_selection(
    *,
    info: dict[str, Any],
    lang: str,
    download_mode: DownloadMode | str,
    video_quality: VideoQuality | str = DEFAULT_VIDEO_QUALITY,
    audio_quality: AudioQuality | str = DEFAULT_AUDIO_QUALITY,
) -> QualitySelection:
    selected_download_mode = normalize_download_mode(download_mode)
    selected_audio_quality = normalize_audio_quality(audio_quality)
    audio_selector, selected_audio_label, audio_notes = _resolve_audio_selector(
        info,
        lang,
        selected_audio_quality,
    )

    if selected_download_mode == DownloadMode.AUDIO:
        return QualitySelection(
            video_quality=None,
            audio_quality=selected_audio_quality,
            format_selector=audio_selector,
            selected_video_label=None,
            selected_audio_label=selected_audio_label,
            notes=audio_notes,
        )

    selected_video_quality = normalize_video_quality(video_quality)
    video_selector, selected_video_label, video_notes = _resolve_video_selector(
        info,
        selected_video_quality,
    )
    return QualitySelection(
        video_quality=selected_video_quality,
        audio_quality=selected_audio_quality,
        format_selector=f"{video_selector}+{audio_selector}",
        selected_video_label=selected_video_label,
        selected_audio_label=selected_audio_label,
        notes=(*video_notes, *audio_notes),
    )


def get_available_video_heights(info: dict[str, Any]) -> tuple[int, ...]:
    heights = {
        height
        for format_info in _format_items(info)
        if _is_video_only_format(format_info)
        for height in [_positive_int(format_info.get("height"))]
        if height is not None
    }
    return tuple(sorted(heights))


def get_audio_quality_candidates(
    info: dict[str, Any],
    lang: str,
) -> tuple[AudioQualityCandidate, ...]:
    candidates: list[AudioQualityCandidate] = []
    for format_info in _format_items(info):
        if not _is_audio_format(format_info, lang):
            continue

        bitrate, bitrate_field = _audio_bitrate(format_info)
        format_id = format_info.get("format_id")
        ext = format_info.get("ext")
        acodec = format_info.get("acodec")
        candidates.append(
            AudioQualityCandidate(
                format_id=(
                    format_id if isinstance(format_id, str) and format_id else None
                ),
                bitrate_kbps=bitrate,
                bitrate_field=bitrate_field,
                ext=ext if isinstance(ext, str) and ext else None,
                acodec=acodec if isinstance(acodec, str) and acodec else None,
            )
        )
    return tuple(candidates)


def format_video_quality_labels(heights: tuple[int, ...]) -> tuple[str, ...]:
    return tuple(f"{height}p" for height in heights)


def format_audio_quality_labels(
    candidates: tuple[AudioQualityCandidate, ...],
) -> tuple[str, ...]:
    bitrates = sorted(
        {
            candidate.bitrate_kbps
            for candidate in candidates
            if candidate.bitrate_kbps is not None
        }
    )
    labels = [_format_bitrate(bitrate) for bitrate in bitrates]
    unknown_count = sum(1 for candidate in candidates if candidate.bitrate_kbps is None)
    if unknown_count == 1:
        labels.append("unknown bitrate")
    elif unknown_count:
        labels.append(f"unknown bitrate ({unknown_count} streams)")
    return tuple(labels)


def _resolve_video_selector(
    info: dict[str, Any],
    video_quality: VideoQuality,
) -> tuple[str, str, tuple[str, ...]]:
    if video_quality.kind == VideoQualityKind.BEST:
        return "bv", video_quality.label, ()

    heights = get_available_video_heights(info)
    if not heights:
        raise QualityError(
            "No usable video qualities were found. Try `--video-quality best` "
            "or inspect the URL with `dbdvdl qualities`."
        )

    if video_quality.kind == VideoQualityKind.MEDIUM:
        height = _closest_height(heights, MEDIUM_VIDEO_TARGET_HEIGHT)
        return _video_height_selector(height), f"{height}p", ()

    if video_quality.kind == VideoQualityKind.LOW:
        height = heights[0]
        return _video_height_selector(height), f"{height}p", ()

    assert video_quality.height is not None
    if video_quality.height not in heights:
        available = ", ".join(format_video_quality_labels(heights))
        raise QualityError(
            f"Requested video quality {video_quality.label} is not available. "
            f"Available video qualities: {available}."
        )
    return _video_height_selector(video_quality.height), video_quality.label, ()


def _resolve_audio_selector(
    info: dict[str, Any],
    lang: str,
    audio_quality: AudioQuality,
) -> tuple[str, str, tuple[str, ...]]:
    candidates = get_audio_quality_candidates(info, lang)
    if not candidates:
        raise QualityError(f"No audio streams found for language `{lang}`.")

    language_filter = _selector_filter("language", lang)
    if audio_quality.kind == AudioQualityKind.BEST:
        return f"bestaudio{language_filter}", audio_quality.label, ()

    candidates_with_bitrate = [
        candidate for candidate in candidates if candidate.bitrate_kbps is not None
    ]
    if not candidates_with_bitrate:
        if audio_quality.kind == AudioQualityKind.MEDIUM:
            return (
                f"bestaudio{language_filter}",
                "best",
                (
                    "Audio quality medium fell back to best because bitrate "
                    "metadata is unavailable.",
                ),
            )
        return (
            f"worstaudio{language_filter}",
            audio_quality.label,
            (
                "Audio quality low is using yt-dlp's worst matching audio because "
                "bitrate metadata is unavailable.",
            ),
        )

    if audio_quality.kind == AudioQualityKind.MEDIUM:
        selected = min(
            candidates_with_bitrate,
            key=lambda candidate: (
                abs(candidate.bitrate_kbps - MEDIUM_AUDIO_TARGET_KBPS),
                candidate.bitrate_kbps,
            ),
        )
    else:
        selected = min(
            candidates_with_bitrate,
            key=lambda candidate: candidate.bitrate_kbps,
        )

    return (
        _audio_candidate_selector(lang, selected, audio_quality),
        _format_bitrate(selected.bitrate_kbps),
        (),
    )


def _audio_candidate_selector(
    lang: str,
    candidate: AudioQualityCandidate,
    audio_quality: AudioQuality,
) -> str:
    language_filter = _selector_filter("language", lang)
    if candidate.format_id:
        format_id_filter = _selector_filter("format_id", candidate.format_id)
        return f"bestaudio{language_filter}{format_id_filter}"
    if candidate.bitrate_kbps is not None and candidate.bitrate_field:
        return (
            f"bestaudio{language_filter}"
            f"[{candidate.bitrate_field}={_format_number(candidate.bitrate_kbps)}]"
        )
    fallback = (
        "worstaudio"
        if audio_quality.kind == AudioQualityKind.LOW
        else "bestaudio"
    )
    return f"{fallback}{language_filter}"


def _video_height_selector(height: int) -> str:
    return f"bv[height={height}]"


def _closest_height(heights: tuple[int, ...], target: int) -> int:
    return min(heights, key=lambda height: (abs(height - target), height))


def _format_items(info: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    formats = info.get("formats", [])
    if not isinstance(formats, list):
        return ()
    return tuple(format_info for format_info in formats if isinstance(format_info, dict))


def _is_video_only_format(format_info: dict[str, Any]) -> bool:
    return (
        format_info.get("vcodec") not in (None, "none")
        and format_info.get("acodec") == "none"
    )


def _is_audio_format(format_info: dict[str, Any], lang: str) -> bool:
    return (
        format_info.get("vcodec") == "none"
        and format_info.get("acodec") not in (None, "none")
        and format_info.get("language") == lang
    )


def _audio_bitrate(format_info: dict[str, Any]) -> tuple[float | None, str | None]:
    for field in ("abr", "tbr"):
        bitrate = _positive_number(format_info.get(field))
        if bitrate is not None:
            return bitrate, field
    return None, None


def _positive_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value > 0:
        return value
    return None


def _positive_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and value > 0:
        return float(value)
    return None


def _selector_filter(field: str, value: str) -> str:
    return f"[{field}={_quote_selector_string(value)}]"


def _quote_selector_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _format_bitrate(value: float | None) -> str:
    if value is None:
        return "unknown bitrate"
    return f"{_format_number(value)}k"


def _format_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:g}"


def _video_quality_error(key: str) -> str:
    return (
        f"{key} must be `best`, `medium`, `low`, or a video resolution from "
        f"{MIN_VIDEO_HEIGHT}p through {MAX_VIDEO_HEIGHT}p."
    )


def _audio_quality_error(key: str) -> str:
    return f"{key} must be `best`, `medium`, or `low`."
