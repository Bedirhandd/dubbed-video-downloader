from __future__ import annotations

from enum import Enum
from typing import Any


class DownloadMode(str, Enum):
    VIDEO = "video"
    AUDIO = "audio"


def normalize_download_mode(value: Any, *, key: str = "download_mode") -> DownloadMode:
    if isinstance(value, DownloadMode):
        return value
    if not isinstance(value, str):
        raise ValueError(f"{key} must be `video` or `audio`.")

    text = value.strip()
    if not text:
        raise ValueError(f"{key} must be `video` or `audio`.")

    try:
        return DownloadMode(text)
    except ValueError as exc:
        raise ValueError(f"{key} must be `video` or `audio`.") from exc
