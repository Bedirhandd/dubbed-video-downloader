from __future__ import annotations

import pytest

from dubbed_video_downloader import errors, quality
from dubbed_video_downloader.download_mode import DownloadMode

VIDEO_AUDIO_INFO: dict[str, list[dict[str, object]]] = {
    "formats": [
        {
            "format_id": "v-480",
            "vcodec": "vp9",
            "acodec": "none",
            "height": 480,
        },
        {
            "format_id": "v-720",
            "vcodec": "vp9",
            "acodec": "none",
            "height": 720,
        },
        {
            "format_id": "tr-low",
            "vcodec": "none",
            "acodec": "opus",
            "language": "tr",
            "abr": 64,
        },
        {
            "format_id": "tr-mid",
            "vcodec": "none",
            "acodec": "mp4a",
            "language": "tr",
            "tbr": 128,
        },
        {
            "format_id": "tr-high",
            "vcodec": "none",
            "acodec": "opus",
            "language": "tr",
            "abr": 160,
        },
    ]
}

PROGRESSIVE_ONLY_INFO: dict[str, list[dict[str, object]]] = {
    "formats": [
        {
            "format_id": "progressive-720",
            "vcodec": "avc1.64001f",
            "acodec": "mp4a.40.2",
            "height": 720,
        },
        {
            "format_id": "tr-audio",
            "vcodec": "none",
            "acodec": "opus",
            "language": "tr",
        },
    ]
}

NO_BITRATE_AUDIO_INFO: dict[str, list[dict[str, object]]] = {
    "formats": [
        {
            "format_id": "tr-audio",
            "vcodec": "none",
            "acodec": "opus",
            "language": "tr",
            "ext": "webm",
        }
    ]
}


def test_video_quality_exact_requires_height() -> None:
    with pytest.raises(ValueError, match="exact video quality requires a height"):
        quality.VideoQuality(quality.VideoQualityKind.EXACT)


def test_video_quality_preset_rejects_height() -> None:
    with pytest.raises(
        ValueError, match="preset video quality must not include a height"
    ):
        quality.VideoQuality(quality.VideoQualityKind.BEST, height=720)


@pytest.mark.parametrize("height", [143, 8641])
def test_video_quality_exact_rejects_out_of_range_height(height: int) -> None:
    with pytest.raises(ValueError, match="video height must be between"):
        quality.VideoQuality(quality.VideoQualityKind.EXACT, height)


def test_video_quality_label_and_str() -> None:
    exact = quality.VideoQuality(quality.VideoQualityKind.EXACT, 720)
    preset = quality.VideoQuality(quality.VideoQualityKind.BEST)

    assert exact.label == "720p"
    assert str(exact) == "720p"
    assert preset.label == "best"
    assert str(preset) == "best"


def test_audio_quality_label_and_str() -> None:
    audio = quality.AudioQuality(quality.AudioQualityKind.MEDIUM)

    assert audio.label == "medium"
    assert str(audio) == "medium"


def test_normalize_video_quality_accepts_presets_and_exact() -> None:
    assert quality.normalize_video_quality("best").kind == quality.VideoQualityKind.BEST
    assert quality.normalize_video_quality(" MEDIUM ").kind == (
        quality.VideoQualityKind.MEDIUM
    )
    assert quality.normalize_video_quality("720P").label == "720p"


def test_normalize_video_quality_passes_through_instance() -> None:
    value = quality.VideoQuality(quality.VideoQualityKind.LOW)
    assert quality.normalize_video_quality(value) is value


@pytest.mark.parametrize("value", ["1p", "abc", "720 p"])
def test_normalize_video_quality_rejects_invalid_values(value: str) -> None:
    with pytest.raises(errors.QualityError, match="video_quality must be"):
        quality.normalize_video_quality(value)


@pytest.mark.parametrize("value", [None, True, ["720p"]])
def test_normalize_video_quality_rejects_non_string(value: object) -> None:
    with pytest.raises(errors.QualityError, match="video_quality must be"):
        quality.normalize_video_quality(value)


def test_normalize_video_quality_rejects_out_of_range_exact() -> None:
    with pytest.raises(errors.QualityError, match="between 144p and 8640p"):
        quality.normalize_video_quality("10000p")


def test_normalize_audio_quality_accepts_presets() -> None:
    assert quality.normalize_audio_quality("best").kind == quality.AudioQualityKind.BEST
    assert quality.normalize_audio_quality(" LOW ").kind == quality.AudioQualityKind.LOW


def test_normalize_audio_quality_passes_through_instance() -> None:
    value = quality.AudioQuality(quality.AudioQualityKind.MEDIUM)
    assert quality.normalize_audio_quality(value) is value


@pytest.mark.parametrize("value", ["128k", "720p", "abc"])
def test_normalize_audio_quality_rejects_invalid_values(value: str) -> None:
    with pytest.raises(errors.QualityError, match="audio_quality must be"):
        quality.normalize_audio_quality(value)


def test_get_available_video_heights_ignores_progressive_formats() -> None:
    assert quality.get_available_video_heights(VIDEO_AUDIO_INFO) == (480, 720)


def test_get_available_video_heights_handles_invalid_formats() -> None:
    info = {
        "formats": [
            "not-a-dict",
            {"vcodec": "vp9", "acodec": "none", "height": 0},
            {"vcodec": "vp9", "acodec": "none", "height": True},
            {"vcodec": "vp9", "acodec": "none", "height": 360},
        ]
    }

    assert quality.get_available_video_heights(info) == (360,)


def test_get_available_video_heights_returns_empty_when_formats_missing() -> None:
    assert quality.get_available_video_heights({}) == ()
    assert quality.get_available_video_heights({"formats": "invalid"}) == ()


def test_get_audio_quality_candidates_prefers_abr_over_tbr() -> None:
    info = {
        "formats": [
            {
                "format_id": "tr-audio",
                "vcodec": "none",
                "acodec": "opus",
                "language": "tr",
                "abr": 96,
                "tbr": 128,
            }
        ]
    }

    candidates = quality.get_audio_quality_candidates(info, "tr")

    assert len(candidates) == 1
    assert candidates[0].bitrate_kbps == 96.0
    assert candidates[0].bitrate_field == "abr"


def test_get_audio_quality_candidates_uses_tbr_when_abr_missing() -> None:
    candidates = quality.get_audio_quality_candidates(VIDEO_AUDIO_INFO, "tr")
    mid = next(candidate for candidate in candidates if candidate.format_id == "tr-mid")

    assert mid.bitrate_kbps == 128.0
    assert mid.bitrate_field == "tbr"


def test_get_audio_quality_candidates_ignores_other_languages() -> None:
    assert quality.get_audio_quality_candidates(VIDEO_AUDIO_INFO, "en") == ()


def test_get_audio_quality_candidates_matches_padded_language() -> None:
    info = {
        "formats": [
            {
                "format_id": "en-audio",
                "vcodec": "none",
                "acodec": "opus",
                "language": " en ",
                "abr": 128,
            }
        ]
    }

    candidates = quality.get_audio_quality_candidates(info, "en")

    assert len(candidates) == 1
    assert candidates[0].format_id == "en-audio"


def test_get_audio_quality_candidates_matches_metadata_language_case_insensitively() -> (
    None
):
    info = {
        "formats": [
            {
                "format_id": "en-us-high",
                "vcodec": "none",
                "acodec": "opus",
                "language": "en-US",
                "abr": 160,
            },
            {
                "format_id": "en-us-low",
                "vcodec": "none",
                "acodec": "opus",
                "language": "en-us",
                "abr": 64,
            },
        ]
    }

    candidates = quality.get_audio_quality_candidates(info, "en-US")

    assert {candidate.format_id for candidate in candidates} == {
        "en-us-high",
        "en-us-low",
    }


def test_get_audio_quality_candidates_matches_resolved_lang_against_different_casing() -> (
    None
):
    info = {
        "formats": [
            {
                "format_id": "en-us-audio",
                "vcodec": "none",
                "acodec": "opus",
                "language": "en-US",
                "abr": 128,
            }
        ]
    }

    candidates = quality.get_audio_quality_candidates(info, "en-us")

    assert len(candidates) == 1
    assert candidates[0].format_id == "en-us-audio"


def test_get_audio_quality_candidates_treats_empty_format_id_as_none() -> None:
    info = {
        "formats": [
            {
                "format_id": "",
                "vcodec": "none",
                "acodec": "opus",
                "language": "tr",
                "abr": 64,
            }
        ]
    }

    candidates = quality.get_audio_quality_candidates(info, "tr")

    assert len(candidates) == 1
    assert candidates[0].format_id is None


def test_format_audio_quality_labels_deduplicates_and_sorts() -> None:
    candidates = quality.get_audio_quality_candidates(VIDEO_AUDIO_INFO, "tr")

    assert quality.format_audio_quality_labels(candidates) == ("64k", "128k", "160k")


def test_format_audio_quality_labels_single_unknown() -> None:
    candidates = (
        quality.AudioQualityCandidate(
            format_id="a",
            bitrate_kbps=None,
            bitrate_field=None,
            ext=None,
            acodec=None,
        ),
    )

    assert quality.format_audio_quality_labels(candidates) == ("unknown bitrate",)


def test_format_audio_quality_labels_multiple_unknown() -> None:
    candidates = tuple(
        quality.AudioQualityCandidate(
            format_id=f"a-{index}",
            bitrate_kbps=None,
            bitrate_field=None,
            ext=None,
            acodec=None,
        )
        for index in range(2)
    )

    assert quality.format_audio_quality_labels(candidates) == (
        "unknown bitrate (2 streams)",
    )


def test_format_audio_quality_labels_all_unknown() -> None:
    candidates = tuple(
        quality.AudioQualityCandidate(
            format_id="a",
            bitrate_kbps=None,
            bitrate_field=None,
            ext=None,
            acodec=None,
        )
        for _ in range(3)
    )

    assert quality.format_audio_quality_labels(candidates) == (
        "unknown bitrate (3 streams)",
    )


def test_resolve_quality_selection_stable_for_normal_metadata() -> None:
    selection = quality.resolve_quality_selection(
        info=VIDEO_AUDIO_INFO,
        lang="tr",
        download_mode=DownloadMode.VIDEO,
        video_quality="best",
        audio_quality="best",
    )

    assert selection.format_selector == 'bv+bestaudio[language="tr"]'
    assert selection.selected_audio_label == "best"
    assert selection.notes == ()


def test_resolve_quality_selection_video_best() -> None:
    selection = quality.resolve_quality_selection(
        info=VIDEO_AUDIO_INFO,
        lang="tr",
        download_mode=DownloadMode.VIDEO,
        video_quality="best",
        audio_quality="best",
    )

    assert selection.format_selector == 'bv+bestaudio[language="tr"]'
    assert selection.selected_video_label == "best"
    assert selection.selected_audio_label == "best"
    assert selection.video_quality is not None
    assert selection.notes == ()


def test_resolve_quality_selection_video_medium_picks_closest_height() -> None:
    selection = quality.resolve_quality_selection(
        info=VIDEO_AUDIO_INFO,
        lang="tr",
        download_mode=DownloadMode.VIDEO,
        video_quality="medium",
        audio_quality="best",
    )

    assert selection.format_selector == 'bv[height=720]+bestaudio[language="tr"]'
    assert selection.selected_video_label == "720p"


def test_resolve_quality_selection_video_low_picks_smallest_height() -> None:
    selection = quality.resolve_quality_selection(
        info=VIDEO_AUDIO_INFO,
        lang="tr",
        download_mode=DownloadMode.VIDEO,
        video_quality="low",
        audio_quality="best",
    )

    assert selection.format_selector == 'bv[height=480]+bestaudio[language="tr"]'
    assert selection.selected_video_label == "480p"


def test_resolve_quality_selection_video_exact_height() -> None:
    selection = quality.resolve_quality_selection(
        info=VIDEO_AUDIO_INFO,
        lang="tr",
        download_mode=DownloadMode.VIDEO,
        video_quality="720p",
        audio_quality="best",
    )

    assert selection.format_selector == 'bv[height=720]+bestaudio[language="tr"]'
    assert selection.selected_video_label == "720p"


def test_resolve_quality_selection_video_exact_missing_height() -> None:
    with pytest.raises(errors.QualityError) as context:
        quality.resolve_quality_selection(
            info=VIDEO_AUDIO_INFO,
            lang="tr",
            download_mode=DownloadMode.VIDEO,
            video_quality="1080p",
            audio_quality="best",
        )

    message = str(context.value)
    assert "Requested video quality 1080p" in message
    assert "480p, 720p" in message


def test_resolve_quality_selection_video_no_usable_heights() -> None:
    with pytest.raises(
        errors.QualityError, match="No usable video qualities were found"
    ):
        quality.resolve_quality_selection(
            info=PROGRESSIVE_ONLY_INFO,
            lang="tr",
            download_mode=DownloadMode.VIDEO,
            video_quality="720p",
            audio_quality="best",
        )


def test_resolve_quality_selection_audio_best() -> None:
    selection = quality.resolve_quality_selection(
        info=VIDEO_AUDIO_INFO,
        lang="tr",
        download_mode=DownloadMode.AUDIO,
        audio_quality="best",
    )

    assert selection.format_selector == 'bestaudio[language="tr"]'
    assert selection.video_quality is None
    assert selection.selected_video_label is None


def test_resolve_quality_selection_audio_medium_selects_closest_bitrate() -> None:
    selection = quality.resolve_quality_selection(
        info=VIDEO_AUDIO_INFO,
        lang="tr",
        download_mode=DownloadMode.AUDIO,
        audio_quality="medium",
    )

    assert selection.format_selector == ('bestaudio[language="tr"][format_id="tr-mid"]')
    assert selection.selected_audio_label == "128k"


def test_resolve_quality_selection_audio_low_selects_lowest_bitrate() -> None:
    selection = quality.resolve_quality_selection(
        info=VIDEO_AUDIO_INFO,
        lang="tr",
        download_mode=DownloadMode.AUDIO,
        audio_quality="low",
    )

    assert selection.format_selector == ('bestaudio[language="tr"][format_id="tr-low"]')
    assert selection.selected_audio_label == "64k"


def test_resolve_quality_selection_audio_medium_falls_back_without_bitrate() -> None:
    selection = quality.resolve_quality_selection(
        info=NO_BITRATE_AUDIO_INFO,
        lang="tr",
        download_mode=DownloadMode.AUDIO,
        audio_quality="medium",
    )

    assert selection.format_selector == 'bestaudio[language="tr"]'
    assert selection.selected_audio_label == "best"
    assert "bitrate metadata is unavailable" in selection.notes[0]


def test_resolve_quality_selection_audio_low_falls_back_without_bitrate() -> None:
    selection = quality.resolve_quality_selection(
        info=NO_BITRATE_AUDIO_INFO,
        lang="tr",
        download_mode=DownloadMode.AUDIO,
        audio_quality="low",
    )

    assert selection.format_selector == 'worstaudio[language="tr"]'
    assert selection.selected_audio_label == "low"
    assert "bitrate metadata is unavailable" in selection.notes[0]


def test_resolve_quality_selection_audio_missing_language() -> None:
    with pytest.raises(
        errors.QualityError,
        match=r"No audio streams found for language `en`\.",
    ):
        quality.resolve_quality_selection(
            info=VIDEO_AUDIO_INFO,
            lang="en",
            download_mode=DownloadMode.AUDIO,
            audio_quality="best",
        )


def test_audio_candidate_selector_uses_bitrate_field_when_format_id_missing() -> None:
    candidate = quality.AudioQualityCandidate(
        format_id=None,
        bitrate_kbps=128.0,
        bitrate_field="tbr",
        ext="m4a",
        acodec="mp4a",
    )

    selector = quality._audio_candidate_selector(
        "tr",
        candidate,
        quality.AudioQuality(quality.AudioQualityKind.MEDIUM),
    )

    assert selector == 'bestaudio[language="tr"][tbr=128]'


def test_audio_candidate_selector_falls_back_to_worstaudio_for_low() -> None:
    candidate = quality.AudioQualityCandidate(
        format_id=None,
        bitrate_kbps=None,
        bitrate_field=None,
        ext="webm",
        acodec="opus",
    )

    selector = quality._audio_candidate_selector(
        "tr",
        candidate,
        quality.AudioQuality(quality.AudioQualityKind.LOW),
    )

    assert selector == 'worstaudio[language="tr"]'


def test_audio_candidate_selector_falls_back_to_bestaudio_for_medium() -> None:
    candidate = quality.AudioQualityCandidate(
        format_id=None,
        bitrate_kbps=None,
        bitrate_field=None,
        ext="webm",
        acodec="opus",
    )

    selector = quality._audio_candidate_selector(
        "tr",
        candidate,
        quality.AudioQuality(quality.AudioQualityKind.MEDIUM),
    )

    assert selector == 'bestaudio[language="tr"]'


def test_selector_filter_quotes_special_characters() -> None:
    assert quality._selector_filter("language", "en-US") == '[language="en-US"]'
    assert quality._selector_filter("language", 'en"US') == '[language="en\\"US"]'
    assert quality._selector_filter("language", r"en\US") == '[language="en\\\\US"]'
