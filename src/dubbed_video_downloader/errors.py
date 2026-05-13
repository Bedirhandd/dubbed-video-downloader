"""Application-level errors for expected user-facing failures."""

from __future__ import annotations


class DubbedVideoDownloaderError(RuntimeError):
    """Base class for expected operational failures."""


class MetadataExtractionError(DubbedVideoDownloaderError):
    """Raised when video metadata cannot be extracted."""


class LanguageUnavailableError(DubbedVideoDownloaderError):
    """Raised when the requested dubbed language is unavailable."""
