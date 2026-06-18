from __future__ import annotations

import pytest

from dubbed_video_downloader import config, errors, quality


@pytest.mark.parametrize(
    "error_type",
    [
        errors.ConfigError,
        errors.QualityError,
        errors.MetadataExtractionError,
        errors.InvalidLanguageCodeError,
        errors.LanguageNotFoundError,
        errors.DownloadError,
    ],
)
def test_expected_errors_share_application_base_class(
    error_type: type[Exception],
) -> None:
    assert issubclass(error_type, errors.DubbedVideoDownloaderError)


def test_module_error_exports_are_canonical() -> None:
    assert config.ConfigError is errors.ConfigError
    assert quality.QualityError is errors.QualityError


def test_legacy_language_error_name_is_removed() -> None:
    assert not hasattr(errors, "LanguageUnavailableError")


def test_quality_error_uses_application_hierarchy() -> None:
    assert not issubclass(errors.QualityError, ValueError)
