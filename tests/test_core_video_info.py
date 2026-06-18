from __future__ import annotations

from unittest.mock import patch

import pytest
from yt_dlp.utils import YoutubeDLError

from dubbed_video_downloader import core, errors


def test_get_video_info_enables_debug_ytdlp_output() -> None:
    with patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl:
        ydl = youtube_dl.return_value.__enter__.return_value
        ydl.extract_info.return_value = {"formats": []}
        core.get_video_info("https://www.youtube.com/watch?v=EXAMPLE", debug=True)
    opts = youtube_dl.call_args.args[0]
    assert not opts["quiet"]
    assert not opts["no_warnings"]
    assert opts["verbose"]


def test_get_video_info_enables_verbose_ytdlp_output_without_debug() -> None:
    with patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl:
        ydl = youtube_dl.return_value.__enter__.return_value
        ydl.extract_info.return_value = {"formats": []}
        core.get_video_info("https://www.youtube.com/watch?v=EXAMPLE", verbose=True)
    opts = youtube_dl.call_args.args[0]
    assert not opts["quiet"]
    assert not opts["no_warnings"]
    assert not opts["verbose"]


def test_get_video_info_rejects_invalid_network_retry_count() -> None:
    with pytest.raises(ValueError) as context:
        core.get_video_info(
            "https://www.youtube.com/watch?v=EXAMPLE", retry_on_network_failure=-1
        )
    assert "retry_on_network_failure" in str(context.value)


def test_get_video_info_suppresses_warnings_by_default() -> None:
    with patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl:
        ydl = youtube_dl.return_value.__enter__.return_value
        ydl.extract_info.return_value = {"formats": []}
        info = core.get_video_info("https://www.youtube.com/watch?v=EXAMPLE")
    assert info == {"formats": []}
    ydl.extract_info.assert_called_once_with(
        "https://www.youtube.com/watch?v=EXAMPLE", download=False
    )
    opts = youtube_dl.call_args.args[0]
    assert opts["quiet"]
    assert opts["no_warnings"]
    assert not opts["verbose"]
    assert opts["noprogress"]
    assert opts["retries"] == core.DEFAULT_RETRY_ON_NETWORK_FAILURE
    assert opts["fragment_retries"] == core.DEFAULT_RETRY_ON_NETWORK_FAILURE
    assert opts["extractor_retries"] == core.DEFAULT_RETRY_ON_NETWORK_FAILURE
    assert "file_access_retries" not in opts
    assert set(opts["retry_sleep_functions"]) == {"http", "fragment", "extractor"}
    assert callable(opts["retry_sleep_functions"]["http"])


def test_network_retry_sleep_functions_accept_ytdlp_keyword() -> None:
    with patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl:
        ydl = youtube_dl.return_value.__enter__.return_value
        ydl.extract_info.return_value = {"formats": []}
        core.get_video_info("https://www.youtube.com/watch?v=EXAMPLE")
    opts = youtube_dl.call_args.args[0]
    for name, sleep_func in opts["retry_sleep_functions"].items():
        delay = sleep_func(n=0)
        assert isinstance(delay, float), f"{name} retry sleep must return a float"
        assert delay > 0, f"{name} retry sleep must be positive"


def test_get_video_info_uses_custom_network_retry_count() -> None:
    with patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl:
        ydl = youtube_dl.return_value.__enter__.return_value
        ydl.extract_info.return_value = {"formats": []}
        core.get_video_info(
            "https://www.youtube.com/watch?v=EXAMPLE", retry_on_network_failure=2
        )
    opts = youtube_dl.call_args.args[0]
    assert opts["retries"] == 2
    assert opts["fragment_retries"] == 2
    assert opts["extractor_retries"] == 2


def test_get_video_info_wraps_ytdlp_metadata_failures() -> None:
    cause = YoutubeDLError("metadata failed")
    with patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl:
        ydl = youtube_dl.return_value.__enter__.return_value
        ydl.extract_info.side_effect = cause
        with pytest.raises(errors.MetadataExtractionError) as context:
            core.get_video_info("https://www.youtube.com/watch?v=EXAMPLE")
    assert context.value.__cause__ is cause
    assert "Could not extract video metadata" in str(context.value)
    assert "metadata failed" in str(context.value)


@pytest.mark.parametrize("invalid_info", [None, [], "metadata", 42])
def test_get_video_info_rejects_unexpected_metadata_shape(invalid_info: object) -> None:
    with patch("dubbed_video_downloader.core.yt_dlp.YoutubeDL") as youtube_dl:
        ydl = youtube_dl.return_value.__enter__.return_value
        ydl.extract_info.return_value = invalid_info
        with pytest.raises(errors.MetadataExtractionError) as context:
            core.get_video_info("https://www.youtube.com/watch?v=EXAMPLE")
    assert context.value.__cause__ is None
    assert "Could not extract video metadata" in str(context.value)
    assert "unexpected metadata shape" in str(context.value)
