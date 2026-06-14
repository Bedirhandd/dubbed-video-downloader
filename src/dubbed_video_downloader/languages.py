from __future__ import annotations

from dataclasses import dataclass

import langcodes
from langcodes.tag_parser import LanguageTagError

from . import errors
from .yt_dlp_types import InfoDict

MAX_VARIANT_DISTANCE = 10
UNDEFINED_LANGUAGE = "und"


@dataclass(frozen=True)
class AudioLanguageInventory:
    langs: frozenset[str]
    skipped_invalid_count: int
    skipped_invalid_tags: tuple[str, ...]


def normalize_language_code(value: str, *, field: str = "language") -> str:
    """Validate and canonicalize a user-supplied BCP-47 language code."""
    text = value.strip()
    if not text:
        raise errors.InvalidLanguageCodeError(f"{field} must not be empty.")

    try:
        standardized = langcodes.standardize_tag(text)
    except LanguageTagError as exc:
        raise errors.InvalidLanguageCodeError(
            f"{field} is not a valid language code: {text!r}."
        ) from exc

    if not langcodes.tag_is_valid(standardized):
        raise errors.InvalidLanguageCodeError(
            f"{field} is not a valid language code: {text!r}."
        )

    language = langcodes.Language.get(standardized)
    if not language.language or language.language == UNDEFINED_LANGUAGE:
        raise errors.InvalidLanguageCodeError(
            f"{field} must not be undefined (`und`): {text!r}."
        )

    return standardized


def normalize_video_language_tag(raw: str) -> str | None:
    """Return a valid metadata language tag, or None if it should be skipped."""
    text = raw.strip()
    if not text:
        return None

    try:
        standardized = langcodes.standardize_tag(text)
    except LanguageTagError:
        return None

    if not langcodes.tag_is_valid(standardized):
        return None

    language = langcodes.Language.get(standardized)
    if not language.language or language.language == UNDEFINED_LANGUAGE:
        return None

    return raw


def format_language_for_display(tag: str) -> str:
    """Return a standardized BCP-47 tag for CLI display."""
    try:
        return langcodes.standardize_tag(tag)
    except LanguageTagError:
        return tag


def display_language_tags(tags: frozenset[str]) -> tuple[str, ...]:
    """Return sorted unique standardized language tags for display."""
    return tuple(sorted({format_language_for_display(tag) for tag in tags}))


def collect_available_audio_langs(info: InfoDict) -> AudioLanguageInventory:
    """Collect valid audio language tags from video metadata."""
    langs: set[str] = set()
    skipped_invalid_count = 0
    skipped_invalid_tags: list[str] = []

    formats = info.get("formats") or []
    for format_info in formats:
        if not isinstance(format_info, dict):
            continue
        if format_info.get("vcodec") != "none":
            continue
        if format_info.get("acodec") in (None, "none"):
            continue

        raw_language = format_info.get("language")
        if not isinstance(raw_language, str) or not raw_language.strip():
            skipped_invalid_count += 1
            skipped_invalid_tags.append("<missing>")
            continue

        normalized = normalize_video_language_tag(raw_language)
        if normalized is None:
            skipped_invalid_count += 1
            skipped_invalid_tags.append(raw_language.strip())
            continue

        langs.add(raw_language)

    return AudioLanguageInventory(
        langs=frozenset(langs),
        skipped_invalid_count=skipped_invalid_count,
        skipped_invalid_tags=tuple(skipped_invalid_tags),
    )


def skipped_tracks_warning(inventory: AudioLanguageInventory) -> str | None:
    if inventory.skipped_invalid_count <= 0:
        return None
    return (
        f"Skipped {inventory.skipped_invalid_count} audio track(s) with invalid "
        "or undefined language metadata."
    )


def resolve_language_for_video(
    requested: str,
    inventory: AudioLanguageInventory,
    *,
    title: str | None = None,
) -> str:
    """Resolve a canonical user language to a video metadata language tag."""
    if inventory.langs:
        pass
    elif inventory.skipped_invalid_count > 0:
        skipped = ", ".join(_unique_skipped_tags(inventory.skipped_invalid_tags))
        detail = f" (skipped: {skipped})" if skipped else ""
        raise errors.LanguageNotFoundError(
            _language_error_prefix(title)
            + "Audio tracks were found but none have a valid language tag"
            + f"{detail}."
        )
    else:
        raise errors.LanguageNotFoundError(
            _language_error_prefix(title) + "No multi-language audio tracks found."
        )

    requested_key = _metadata_lang_key(requested)
    exact_matches = sorted(
        (
            available
            for available in inventory.langs
            if _metadata_lang_key(available) == requested_key
        ),
        key=_raw_tag_sort_key,
    )
    if exact_matches:
        return exact_matches[0]

    if not _request_requires_exact_match(requested):
        raw_by_standard = _raw_tags_by_standard(inventory.langs)
        resolved_standard = langcodes.closest_supported_match(
            requested,
            sorted(raw_by_standard),
            max_distance=MAX_VARIANT_DISTANCE,
        )
        if resolved_standard is not None:
            return _select_raw_tag(raw_by_standard[resolved_standard], requested_key)

    available_display = ", ".join(display_language_tags(inventory.langs))
    raise errors.LanguageNotFoundError(
        _language_error_prefix(title) + f"Requested dub language not found.\n"
        f"Requested: {requested}\n"
        f"Available: {available_display}"
    )


def _request_requires_exact_match(requested: str) -> bool:
    language = langcodes.Language.get(requested)
    return language.territory is not None or language.script is not None


def _metadata_lang_key(tag: str) -> str:
    return tag.strip().casefold()


def _standardized_metadata_tag(tag: str) -> str:
    stripped = tag.strip()
    try:
        return langcodes.standardize_tag(stripped)
    except LanguageTagError:
        return stripped


def _raw_tag_sort_key(tag: str) -> tuple[int, str]:
    return (len(tag), tag)


def _raw_tags_by_standard(langs: frozenset[str]) -> dict[str, tuple[str, ...]]:
    raw_by_standard: dict[str, list[str]] = {}
    for tag in langs:
        standard = _standardized_metadata_tag(tag)
        raw_by_standard.setdefault(standard, []).append(tag)
    return {
        standard: tuple(sorted(raw_tags, key=_raw_tag_sort_key))
        for standard, raw_tags in raw_by_standard.items()
    }


def _select_raw_tag(raw_tags: tuple[str, ...], requested_key: str) -> str:
    exact_matches = [
        tag for tag in raw_tags if _metadata_lang_key(tag) == requested_key
    ]
    if exact_matches:
        return sorted(exact_matches, key=_raw_tag_sort_key)[0]
    return raw_tags[0]


def _language_error_prefix(title: str | None) -> str:
    if title:
        return f"For '{title}': "
    return ""


def _unique_skipped_tags(tags: tuple[str, ...]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for tag in tags:
        if tag in seen:
            continue
        seen.add(tag)
        unique.append(tag)
    return unique
