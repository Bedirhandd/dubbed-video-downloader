from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from . import quality
from .download_mode import DownloadMode
from .download_mode import normalize_download_mode as _normalize_download_mode
from .errors import ConfigError

CONFIG_DIR_NAME = "dubbed-video-downloader"
CONFIG_FILE_NAME = "config.yaml"
DEFAULT_OUTPUT_DIR = "~/Downloads/dbdvdl-output"
DEFAULT_FFMPEG_PATH = "ffmpeg"
DEFAULT_LANG = "en"
DEFAULT_DOWNLOAD_MODE = DownloadMode.VIDEO
DEFAULT_VIDEO_QUALITY = quality.DEFAULT_VIDEO_QUALITY
DEFAULT_AUDIO_QUALITY = quality.DEFAULT_AUDIO_QUALITY
DEFAULT_RETRY_ON_NETWORK_FAILURE = 3


@dataclass(frozen=True)
class AppConfig:
    output_dir: Path
    ffmpeg_path: str
    default_lang: str
    default_download_mode: DownloadMode
    default_video_quality: quality.VideoQuality
    default_audio_quality: quality.AudioQuality
    retry_on_network_failure: int


def get_config_path() -> Path:
    return get_config_dir() / CONFIG_FILE_NAME


def get_config_dir() -> Path:
    return Path.home() / ".config" / CONFIG_DIR_NAME


def load_config(path: Path | None = None) -> AppConfig:
    config_path = path or get_config_path()
    if not config_path.exists():
        raise ConfigError(
            f"Config file not found at {config_path}. Run `dbdvdl init` to create it."
        )

    try:
        raw_config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"Could not parse {config_path}: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"Could not read {config_path}: {exc}") from exc

    if not isinstance(raw_config, dict):
        raise ConfigError(f"{config_path} must contain a YAML mapping.")

    return config_from_mapping(raw_config, source=config_path)


def config_from_mapping(raw_config: dict[str, Any], source: Path | None = None) -> AppConfig:
    location = str(source) if source else "config"
    missing_keys = [
        key
        for key in ("output_dir", "ffmpeg_path", "default_lang")
        if key not in raw_config
    ]
    if missing_keys:
        missing = ", ".join(missing_keys)
        raise ConfigError(f"{location} is missing required key(s): {missing}.")

    output_dir = _require_string(raw_config["output_dir"], "output_dir", location)
    ffmpeg_path = _require_string(raw_config["ffmpeg_path"], "ffmpeg_path", location)
    default_lang = _require_string(
        raw_config["default_lang"],
        "default_lang",
        location,
    )
    retry_on_network_failure = raw_config.get(
        "retry_on_network_failure",
        DEFAULT_RETRY_ON_NETWORK_FAILURE,
    )
    default_download_mode = raw_config.get(
        "default_download_mode",
        DEFAULT_DOWNLOAD_MODE,
    )
    default_video_quality = raw_config.get(
        "default_video_quality",
        DEFAULT_VIDEO_QUALITY,
    )
    default_audio_quality = raw_config.get(
        "default_audio_quality",
        DEFAULT_AUDIO_QUALITY,
    )

    return AppConfig(
        output_dir=normalize_output_dir(output_dir),
        ffmpeg_path=normalize_ffmpeg_path(ffmpeg_path),
        default_lang=normalize_default_lang(default_lang),
        default_download_mode=normalize_download_mode(default_download_mode),
        default_video_quality=normalize_video_quality(default_video_quality),
        default_audio_quality=normalize_audio_quality(default_audio_quality),
        retry_on_network_failure=normalize_retry_on_network_failure(
            retry_on_network_failure
        ),
    )


def write_config(
    *,
    output_dir: str,
    ffmpeg_path: str,
    default_lang: str,
    default_download_mode: str | DownloadMode = DEFAULT_DOWNLOAD_MODE,
    default_video_quality: str | quality.VideoQuality = DEFAULT_VIDEO_QUALITY,
    default_audio_quality: str | quality.AudioQuality = DEFAULT_AUDIO_QUALITY,
    retry_on_network_failure: int = DEFAULT_RETRY_ON_NETWORK_FAILURE,
    path: Path | None = None,
    overwrite: bool = False,
) -> Path:
    config_path = path or get_config_path()
    if config_path.exists() and not overwrite:
        raise ConfigError(
            f"Config file already exists at {config_path}. Use --force to overwrite it."
        )

    normalize_output_dir(output_dir)
    normalize_ffmpeg_path(ffmpeg_path)
    normalized_default_lang = normalize_default_lang(default_lang)
    normalized_default_download_mode = normalize_download_mode(default_download_mode)
    normalized_default_video_quality = normalize_video_quality(default_video_quality)
    normalized_default_audio_quality = normalize_audio_quality(default_audio_quality)
    normalized_retry_on_network_failure = normalize_retry_on_network_failure(
        retry_on_network_failure
    )

    config_path.parent.mkdir(parents=True, exist_ok=True)
    rendered = yaml.safe_dump(
        {
            "output_dir": output_dir,
            "ffmpeg_path": ffmpeg_path,
            "default_lang": normalized_default_lang,
            "default_download_mode": normalized_default_download_mode.value,
            "default_video_quality": normalized_default_video_quality.label,
            "default_audio_quality": normalized_default_audio_quality.label,
            "retry_on_network_failure": normalized_retry_on_network_failure,
        },
        sort_keys=False,
    )
    config_path.write_text(rendered, encoding="utf-8")
    return config_path


def remove_config_dir(path: Path | None = None) -> Path | None:
    config_dir = path or get_config_dir()
    if not config_dir.exists():
        return None
    if not config_dir.is_dir():
        raise ConfigError(f"{config_dir} exists but is not a directory.")
    shutil.rmtree(config_dir)
    return config_dir


def normalize_output_dir(value: str) -> Path:
    text = _clean_string(value, "output_dir")
    path = Path(_expand_path_text(text))
    if not path.is_absolute():
        raise ConfigError(
            "output_dir must be an absolute path after expansion. "
            "Use ~/Downloads/dbdvdl-output or /path/to/output."
        )
    return path


def normalize_ffmpeg_path(value: str) -> str:
    text = _clean_string(value, "ffmpeg_path")
    expanded = _expand_path_text(text)
    path = Path(expanded)

    if path.is_absolute():
        return str(path)

    if _is_bare_ffmpeg_command(expanded):
        return expanded

    raise ConfigError("ffmpeg_path must be `ffmpeg` or an absolute path.")


def normalize_default_lang(value: str) -> str:
    return _clean_string(value, "default_lang")


def normalize_download_mode(value: Any) -> DownloadMode:
    try:
        return _normalize_download_mode(value, key="default_download_mode")
    except ValueError as exc:
        raise ConfigError(str(exc)) from exc


def normalize_video_quality(value: Any) -> quality.VideoQuality:
    try:
        return quality.normalize_video_quality(value, key="default_video_quality")
    except quality.QualityError as exc:
        raise ConfigError(str(exc)) from exc


def normalize_audio_quality(value: Any) -> quality.AudioQuality:
    try:
        return quality.normalize_audio_quality(value, key="default_audio_quality")
    except quality.QualityError as exc:
        raise ConfigError(str(exc)) from exc


def normalize_retry_on_network_failure(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError("retry_on_network_failure must be a non-negative integer.")
    if value < 0:
        raise ConfigError("retry_on_network_failure must be a non-negative integer.")
    return value


def ffmpeg_location_for_yt_dlp(ffmpeg_path: str) -> str | None:
    if _is_bare_ffmpeg_command(ffmpeg_path):
        return None
    return ffmpeg_path


def _require_string(value: Any, key: str, location: str) -> str:
    if not isinstance(value, str):
        raise ConfigError(f"{location} key `{key}` must be a string.")
    return value


def _clean_string(value: str, key: str) -> str:
    text = value.strip()
    if not text:
        raise ConfigError(f"{key} must not be empty.")
    return text


def _expand_path_text(value: str) -> str:
    return os.path.expandvars(os.path.expanduser(value))


def _is_bare_ffmpeg_command(value: str) -> bool:
    return value in {"ffmpeg", "ffmpeg.exe"}
