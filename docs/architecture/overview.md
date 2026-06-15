# Architecture Overview

## Project Structure

```
dubbed-video-downloader/
├── src/
│   └── dubbed_video_downloader/
│       ├── __init__.py          # Package init, __version__ = "0.1.0"
│       ├── __main__.py          # Entry point: from .cli import app; app()
│       ├── cli.py               # Typer CLI definition, commands, option parsing, output formatting
│       ├── core.py              # Download orchestration, staging, finalization, metadata extraction
│       ├── config.py            # Config file I/O, validation, normalization
│       ├── languages.py         # BCP-47 language code handling, resolution against video metadata
│       ├── quality.py           # Video/audio quality enums, selection logic, format selectors
│       ├── download_mode.py     # DownloadMode enum (video/audio) and normalization
│       ├── exists_behavior.py   # FileExistsBehavior enum (skip/fail/overwrite) and normalization
│       ├── doctor.py            # Environment check logic (Python, FFmpeg, Node, packages)
│       ├── errors.py            # Custom exception hierarchy
│       └── yt_dlp_types.py      # Type aliases for yt-dlp (InfoDict, YdlParams)
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures, network guard, CLI runner, test helpers
│   ├── support/
│   │   ├── __init__.py
│   │   ├── cli_helpers.py       # Helper functions for CLI tests (language inventory builders)
│   │   └── network_guard.py     # TCP socket monkey-patching for offline testing
│   ├── test_cli_download.py
│   ├── test_cli_init.py
│   ├── test_cli_langs.py
│   ├── test_cli_qualities.py
│   ├── test_cli_config_commands.py
│   ├── test_config.py
│   ├── test_core_video_info.py
│   ├── test_core_download.py
│   ├── test_core_plan_download.py
│   ├── test_core_exists_behavior.py
│   ├── test_core_finalize.py
│   ├── test_core_stale_cleanup.py
│   ├── test_doctor.py
│   ├── test_errors.py
│   ├── test_languages.py
│   ├── test_network_guard.py
│   └── test_quality.py
├── pyproject.toml               # Project metadata, dependencies, tool config (ruff, mypy, pytest, coverage)
├── .pre-commit-config.yaml      # Pre-commit hooks (ruff, mypy)
├── .github/
│   ├── workflows/ci.yml         # CI pipeline (lint + test matrix: 3.10, 3.11, 3.12)
│   └── dependabot.yml           # Automated dependency updates (github-actions, uv)
├── README.md
├── README-TR.md
└── CONTRIBUTING.md
```
