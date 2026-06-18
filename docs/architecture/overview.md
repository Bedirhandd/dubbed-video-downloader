# Architecture Overview

## Project Structure

```
dubbed-video-downloader/
├── src/
│   └── dubbed_video_downloader/
│       ├── __init__.py          # Package init, __version__ = "0.2.0"
│       ├── __main__.py          # Module entrypoint: `python -m dubbed_video_downloader`
│       ├── cli.py               # Typer CLI definition, commands, option parsing, output formatting
│       ├── core.py              # Download orchestration, staging, finalization, metadata extraction
│       ├── config.py            # Config file I/O, validation, normalization
│       ├── doctor.py            # Environment check logic (Python, FFmpeg, Node, packages)
│       ├── download_mode.py     # DownloadMode enum (video/audio) and normalization
│       ├── errors.py            # Custom exception hierarchy
│       ├── exists_behavior.py   # FileExistsBehavior enum (skip/fail/overwrite) and normalization
│       ├── languages.py         # BCP-47 language code handling, resolution against video metadata
│       ├── quality.py           # Video/audio quality enums, selection logic, format selectors
│       └── yt_dlp_types.py      # Type aliases for yt-dlp (InfoDict, YdlParams)
├── tests/
│   ├── conftest.py              # Pytest fixtures, network guard, CLI runner, test helpers
│   ├── support/
│   │   ├── cli_helpers.py       # Helper functions for CLI tests (language inventory builders)
│   │   ├── live_helpers.py      # Helper functions for live integration tests
│   │   └── network_guard.py     # TCP socket monkey-patching for offline testing
│   ├── live/
│   │   ├── conftest.py          # Live fixtures, temporary HOME/config, runtime prerequisites
│   │   ├── test_live_download.py
│   │   ├── test_live_matrix.py
│   │   └── test_live_metadata.py
│   ├── fixtures/
│   │   └── vulnerability-audit-negative/
│   │       ├── pyproject.toml   # Intentionally vulnerable audit fixture
│   │       └── uv.lock
│   ├── test_cli_download.py
│   ├── test_cli_init.py
│   ├── test_cli_config_commands.py
│   ├── test_cli_langs.py
│   ├── test_cli_qualities.py
│   ├── test_config.py
│   ├── test_core_download.py
│   ├── test_core_exists_behavior.py
│   ├── test_core_finalize.py
│   ├── test_core_plan_download.py
│   ├── test_core_stale_cleanup.py
│   ├── test_core_video_info.py
│   ├── test_doctor.py
│   ├── test_errors.py
│   ├── test_languages.py
│   ├── test_network_guard.py
│   ├── test_quality.py
│   └── test_version_sync.py     # Regression guard for release metadata/version drift
├── docs/
│   ├── architecture/
│   │   ├── overview.md
│   │   ├── modules.md
│   │   ├── download-pipeline.md
│   │   └── testing.md
│   ├── commands/
│   ├── configuration/
│   ├── faq/
│   ├── features/
│   ├── getting-started/
│   ├── usage-examples/
│   └── index.md
├── scripts/
│   └── test-live.sh             # Wrapper for local live integration tests
├── .github/
│   ├── workflows/
│   │   ├── ci.yml               # Offline lint, audit, and test matrix (3.10, 3.11, 3.12)
│   │   └── release.yml          # Tag-gated verify-and-publish workflow
│   └── dependabot.yml           # Automated dependency updates (github-actions, uv)
├── .pre-commit-config.yaml      # Pre-commit hooks (ruff, mypy)
├── CHANGELOG.md                 # Release history and notable changes
├── CONTRIBUTING.md              # Branch, commit, PR, and verification conventions
├── LICENSE
├── README.md                    # Main repository overview
├── README-PYPI.md               # Long description published to PyPI
├── README-TR.md                 # Turkish repository overview
├── SECURITY.md                  # Vulnerability reporting and supported-version policy
├── pyproject.toml               # Package metadata, exact direct deps, and tool config
└── uv.lock                      # Resolved dependency graph used by CI and local development
```

This is a curated snapshot of the contributor- and release-relevant layout rather
than an exhaustive listing of every file in the repository.
