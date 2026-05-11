from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR_NAME = "dubbed-video-downloader"
CONFIG_FILE_NAME = "config.yaml"
DEFAULT_OUTPUT_DIR = "~/Downloads/dbdvdl-output"
DEFAULT_FFMPEG_PATH = "ffmpeg"


@dataclass(frozen=True)
class AppConfig:
    output_dir: Path
    ffmpeg_path: str


class ConfigError(RuntimeError):
    """Raised when the user config is missing or invalid."""


def get_config_path() -> Path:
    return Path.home() / ".config" / CONFIG_DIR_NAME / CONFIG_FILE_NAME


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
        key for key in ("output_dir", "ffmpeg_path") if key not in raw_config
    ]
    if missing_keys:
        missing = ", ".join(missing_keys)
        raise ConfigError(f"{location} is missing required key(s): {missing}.")

    output_dir = _require_string(raw_config["output_dir"], "output_dir", location)
    ffmpeg_path = _require_string(raw_config["ffmpeg_path"], "ffmpeg_path", location)

    return AppConfig(
        output_dir=normalize_output_dir(output_dir),
        ffmpeg_path=normalize_ffmpeg_path(ffmpeg_path),
    )


def write_config(
    *,
    output_dir: str,
    ffmpeg_path: str,
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

    config_path.parent.mkdir(parents=True, exist_ok=True)
    rendered = yaml.safe_dump(
        {
            "output_dir": output_dir,
            "ffmpeg_path": ffmpeg_path,
        },
        sort_keys=False,
    )
    config_path.write_text(rendered, encoding="utf-8")
    return config_path


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
