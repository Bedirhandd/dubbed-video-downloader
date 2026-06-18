"""Application-level errors for expected user-facing failures."""

from __future__ import annotations


class DubbedVideoDownloaderError(RuntimeError):
    """Base class for expected operational failures."""


class ConfigError(DubbedVideoDownloaderError):
    """Raised when the user config is missing or invalid."""


class QualityError(DubbedVideoDownloaderError):
    """Raised when quality input or metadata cannot produce a safe selector."""


class MetadataExtractionError(DubbedVideoDownloaderError):
    """Raised when video metadata cannot be extracted."""


class InvalidLanguageCodeError(DubbedVideoDownloaderError):
    """Raised when a user-supplied language code is invalid."""


class LanguageNotFoundError(DubbedVideoDownloaderError):
    """Raised when the requested dubbed language is unavailable."""


class DownloadError(DubbedVideoDownloaderError):
    """Raised when media download or download planning fails."""
