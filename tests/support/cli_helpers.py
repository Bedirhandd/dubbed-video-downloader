from __future__ import annotations

import re

from dubbed_video_downloader import languages


def plain_cli_output(text: str) -> str:
    without_ansi = re.sub(r"\x1b\[[0-9;]*m", "", text)
    return without_ansi.replace("\n", " ")


def audio_inventory(
    *langs: str,
    skipped_invalid_count: int = 0,
    skipped_invalid_tags: tuple[str, ...] = (),
) -> languages.AudioLanguageInventory:
    return languages.AudioLanguageInventory(
        langs=frozenset(langs),
        skipped_invalid_count=skipped_invalid_count,
        skipped_invalid_tags=skipped_invalid_tags,
    )
