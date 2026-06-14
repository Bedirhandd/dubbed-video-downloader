from __future__ import annotations

import pytest

from dubbed_video_downloader import errors, languages


def test_normalize_language_code_accepts_common_aliases() -> None:
    assert languages.normalize_language_code("eng") == "en"
    assert languages.normalize_language_code("EN-us") == "en-US"
    assert languages.normalize_language_code("en_uk") == "en-GB"
    assert languages.normalize_language_code("tr") == "tr"


@pytest.mark.parametrize("value", ["", " ", "jp", "und"])
def test_normalize_language_code_rejects_invalid_values(value: str) -> None:
    with pytest.raises(errors.InvalidLanguageCodeError):
        languages.normalize_language_code(value)


def test_collect_available_audio_langs_skips_invalid_tracks() -> None:
    inventory = languages.collect_available_audio_langs(
        {
            "formats": [
                {
                    "vcodec": "none",
                    "acodec": "opus",
                    "language": "en",
                },
                {
                    "vcodec": "none",
                    "acodec": "opus",
                    "language": "tr",
                },
                {
                    "vcodec": "none",
                    "acodec": "opus",
                    "language": "und",
                },
            ]
        }
    )

    assert inventory.langs == frozenset({"en", "tr"})
    assert inventory.skipped_invalid_count == 1
    assert inventory.skipped_invalid_tags == ("und",)


def test_collect_available_audio_langs_only_und_fails_on_resolve() -> None:
    inventory = languages.collect_available_audio_langs(
        {
            "formats": [
                {
                    "vcodec": "none",
                    "acodec": "opus",
                    "language": "und",
                }
            ]
        }
    )

    assert inventory.langs == frozenset()
    assert inventory.skipped_invalid_count == 1
    with pytest.raises(
        errors.LanguageNotFoundError,
        match="none have a valid language tag",
    ):
        languages.resolve_language_for_video("en", inventory)


def test_resolve_language_for_video_matches_variants() -> None:
    inventory = languages.AudioLanguageInventory(
        langs=frozenset({"en-US"}),
        skipped_invalid_count=0,
        skipped_invalid_tags=(),
    )

    assert languages.resolve_language_for_video("en", inventory) == "en-US"


def test_resolve_language_for_video_rejects_cross_language_match() -> None:
    inventory = languages.AudioLanguageInventory(
        langs=frozenset({"en"}),
        skipped_invalid_count=0,
        skipped_invalid_tags=(),
    )

    with pytest.raises(errors.LanguageNotFoundError):
        languages.resolve_language_for_video("tr", inventory)


def test_resolve_language_for_video_matches_padded_metadata_tag() -> None:
    inventory = languages.AudioLanguageInventory(
        langs=frozenset({" en "}),
        skipped_invalid_count=0,
        skipped_invalid_tags=(),
    )

    assert languages.resolve_language_for_video("en", inventory) == " en "


def test_resolve_language_for_video_prefers_shorter_exact_stripped_match() -> None:
    inventory = languages.AudioLanguageInventory(
        langs=frozenset({" en ", "en"}),
        skipped_invalid_count=0,
        skipped_invalid_tags=(),
    )

    assert languages.resolve_language_for_video("en", inventory) == "en"


def test_resolve_language_for_video_rejects_cross_regional_match() -> None:
    inventory = languages.AudioLanguageInventory(
        langs=frozenset({"en-GB"}),
        skipped_invalid_count=0,
        skipped_invalid_tags=(),
    )

    with pytest.raises(errors.LanguageNotFoundError):
        languages.resolve_language_for_video("en-AU", inventory)


def test_resolve_language_for_video_rejects_regional_request_with_base_only() -> None:
    inventory = languages.AudioLanguageInventory(
        langs=frozenset({"en"}),
        skipped_invalid_count=0,
        skipped_invalid_tags=(),
    )

    with pytest.raises(errors.LanguageNotFoundError):
        languages.resolve_language_for_video("en-AU", inventory)


def test_resolve_language_for_video_rejects_cross_portuguese_regional_match() -> None:
    inventory = languages.AudioLanguageInventory(
        langs=frozenset({"pt-PT"}),
        skipped_invalid_count=0,
        skipped_invalid_tags=(),
    )

    with pytest.raises(errors.LanguageNotFoundError):
        languages.resolve_language_for_video("pt-BR", inventory)


def test_resolve_language_for_video_accepts_exact_regional_match() -> None:
    inventory = languages.AudioLanguageInventory(
        langs=frozenset({"en-AU"}),
        skipped_invalid_count=0,
        skipped_invalid_tags=(),
    )

    assert languages.resolve_language_for_video("en-AU", inventory) == "en-AU"


def test_resolve_language_for_video_accepts_padded_regional_match() -> None:
    inventory = languages.AudioLanguageInventory(
        langs=frozenset({" en-gb "}),
        skipped_invalid_count=0,
        skipped_invalid_tags=(),
    )

    assert languages.resolve_language_for_video("en-GB", inventory) == " en-gb "


def test_resolve_language_for_video_rejects_cross_script_match() -> None:
    inventory = languages.AudioLanguageInventory(
        langs=frozenset({"zh-Hant"}),
        skipped_invalid_count=0,
        skipped_invalid_tags=(),
    )

    with pytest.raises(errors.LanguageNotFoundError):
        languages.resolve_language_for_video("zh-Hans", inventory)


def test_resolve_language_for_video_matches_base_language_to_script_variant() -> None:
    inventory = languages.AudioLanguageInventory(
        langs=frozenset({"zh-Hans"}),
        skipped_invalid_count=0,
        skipped_invalid_tags=(),
    )

    assert languages.resolve_language_for_video("zh", inventory) == "zh-Hans"
