from __future__ import annotations

from enum import Enum
from typing import Any


class FileExistsBehavior(str, Enum):
    SKIP = "skip"
    FAIL = "fail"
    OVERWRITE = "overwrite"


def normalize_exists_behavior(
    value: Any,
    *,
    key: str = "exists_behavior",
) -> FileExistsBehavior:
    if isinstance(value, FileExistsBehavior):
        return value
    if not isinstance(value, str):
        raise ValueError(f"{key} must be `skip`, `fail`, or `overwrite`.")

    text = value.strip()
    if not text:
        raise ValueError(f"{key} must be `skip`, `fail`, or `overwrite`.")

    try:
        return FileExistsBehavior(text)
    except ValueError as exc:
        raise ValueError(f"{key} must be `skip`, `fail`, or `overwrite`.") from exc
