from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from yt_dlp import _Params as YdlParams
    from yt_dlp.extractor.common import _InfoDict as InfoDict
else:
    YdlParams = dict[str, Any]
    InfoDict = dict[str, Any]

__all__ = ["InfoDict", "YdlParams"]
