from __future__ import annotations

import unittest

from dubbed_video_downloader import config
from dubbed_video_downloader import errors
from dubbed_video_downloader import quality


class ErrorTests(unittest.TestCase):
    def test_expected_errors_share_application_base_class(self) -> None:
        for error_type in (
            errors.ConfigError,
            errors.QualityError,
            errors.MetadataExtractionError,
            errors.LanguageNotFoundError,
            errors.DownloadError,
        ):
            with self.subTest(error_type=error_type):
                self.assertTrue(
                    issubclass(error_type, errors.DubbedVideoDownloaderError)
                )

    def test_module_error_exports_are_canonical(self) -> None:
        self.assertIs(config.ConfigError, errors.ConfigError)
        self.assertIs(quality.QualityError, errors.QualityError)

    def test_legacy_language_error_name_is_removed(self) -> None:
        self.assertFalse(hasattr(errors, "LanguageUnavailableError"))

    def test_quality_error_uses_application_hierarchy(self) -> None:
        self.assertFalse(issubclass(errors.QualityError, ValueError))


if __name__ == "__main__":
    unittest.main()
