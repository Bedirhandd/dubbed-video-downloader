from __future__ import annotations

import unittest

from dubbed_video_downloader import errors
from dubbed_video_downloader import languages


class LanguageTests(unittest.TestCase):
    def test_normalize_language_code_accepts_common_aliases(self) -> None:
        self.assertEqual(languages.normalize_language_code("eng"), "en")
        self.assertEqual(languages.normalize_language_code("EN-us"), "en-US")
        self.assertEqual(languages.normalize_language_code("en_uk"), "en-GB")
        self.assertEqual(languages.normalize_language_code("tr"), "tr")

    def test_normalize_language_code_rejects_invalid_values(self) -> None:
        for value in ("", " ", "jp", "und"):
            with self.subTest(value=value):
                with self.assertRaises(errors.InvalidLanguageCodeError):
                    languages.normalize_language_code(value)

    def test_collect_available_audio_langs_skips_invalid_tracks(self) -> None:
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

        self.assertEqual(inventory.langs, frozenset({"en", "tr"}))
        self.assertEqual(inventory.skipped_invalid_count, 1)
        self.assertEqual(inventory.skipped_invalid_tags, ("und",))

    def test_collect_available_audio_langs_only_und_fails_on_resolve(self) -> None:
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

        self.assertEqual(inventory.langs, frozenset())
        self.assertEqual(inventory.skipped_invalid_count, 1)
        with self.assertRaises(errors.LanguageNotFoundError) as context:
            languages.resolve_language_for_video("en", inventory)
        self.assertIn("none have a valid language tag", str(context.exception))

    def test_resolve_language_for_video_matches_variants(self) -> None:
        inventory = languages.AudioLanguageInventory(
            langs=frozenset({"en-US"}),
            skipped_invalid_count=0,
            skipped_invalid_tags=(),
        )

        self.assertEqual(
            languages.resolve_language_for_video("en", inventory),
            "en-US",
        )

    def test_resolve_language_for_video_rejects_cross_language_match(self) -> None:
        inventory = languages.AudioLanguageInventory(
            langs=frozenset({"en"}),
            skipped_invalid_count=0,
            skipped_invalid_tags=(),
        )

        with self.assertRaises(errors.LanguageNotFoundError):
            languages.resolve_language_for_video("tr", inventory)

    def test_resolve_language_for_video_matches_padded_metadata_tag(self) -> None:
        inventory = languages.AudioLanguageInventory(
            langs=frozenset({" en "}),
            skipped_invalid_count=0,
            skipped_invalid_tags=(),
        )

        self.assertEqual(
            languages.resolve_language_for_video("en", inventory),
            " en ",
        )

    def test_resolve_language_for_video_prefers_shorter_exact_stripped_match(self) -> None:
        inventory = languages.AudioLanguageInventory(
            langs=frozenset({" en ", "en"}),
            skipped_invalid_count=0,
            skipped_invalid_tags=(),
        )

        self.assertEqual(
            languages.resolve_language_for_video("en", inventory),
            "en",
        )

    def test_resolve_language_for_video_rejects_cross_regional_match(self) -> None:
        inventory = languages.AudioLanguageInventory(
            langs=frozenset({"en-GB"}),
            skipped_invalid_count=0,
            skipped_invalid_tags=(),
        )

        with self.assertRaises(errors.LanguageNotFoundError):
            languages.resolve_language_for_video("en-AU", inventory)

    def test_resolve_language_for_video_rejects_regional_request_with_base_only(
        self,
    ) -> None:
        inventory = languages.AudioLanguageInventory(
            langs=frozenset({"en"}),
            skipped_invalid_count=0,
            skipped_invalid_tags=(),
        )

        with self.assertRaises(errors.LanguageNotFoundError):
            languages.resolve_language_for_video("en-AU", inventory)

    def test_resolve_language_for_video_rejects_cross_portuguese_regional_match(
        self,
    ) -> None:
        inventory = languages.AudioLanguageInventory(
            langs=frozenset({"pt-PT"}),
            skipped_invalid_count=0,
            skipped_invalid_tags=(),
        )

        with self.assertRaises(errors.LanguageNotFoundError):
            languages.resolve_language_for_video("pt-BR", inventory)

    def test_resolve_language_for_video_accepts_exact_regional_match(self) -> None:
        inventory = languages.AudioLanguageInventory(
            langs=frozenset({"en-AU"}),
            skipped_invalid_count=0,
            skipped_invalid_tags=(),
        )

        self.assertEqual(
            languages.resolve_language_for_video("en-AU", inventory),
            "en-AU",
        )

    def test_resolve_language_for_video_accepts_padded_regional_match(self) -> None:
        inventory = languages.AudioLanguageInventory(
            langs=frozenset({" en-gb "}),
            skipped_invalid_count=0,
            skipped_invalid_tags=(),
        )

        self.assertEqual(
            languages.resolve_language_for_video("en-GB", inventory),
            " en-gb ",
        )

    def test_resolve_language_for_video_rejects_cross_script_match(self) -> None:
        inventory = languages.AudioLanguageInventory(
            langs=frozenset({"zh-Hant"}),
            skipped_invalid_count=0,
            skipped_invalid_tags=(),
        )

        with self.assertRaises(errors.LanguageNotFoundError):
            languages.resolve_language_for_video("zh-Hans", inventory)

    def test_resolve_language_for_video_matches_base_language_to_script_variant(
        self,
    ) -> None:
        inventory = languages.AudioLanguageInventory(
            langs=frozenset({"zh-Hans"}),
            skipped_invalid_count=0,
            skipped_invalid_tags=(),
        )

        self.assertEqual(
            languages.resolve_language_for_video("zh", inventory),
            "zh-Hans",
        )


if __name__ == "__main__":
    unittest.main()
