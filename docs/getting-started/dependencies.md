# Dependencies

This page lists every dependency of the project, categorized by purpose.

## Runtime Dependencies (Production)

These packages are required to run `dbdvdl`. They are installed automatically when you run `pipx install dubbed-video-downloader` or `pip install dubbed-video-downloader`.

The project exact-pins its direct runtime, development, and build dependencies in `pyproject.toml`. The versions below reflect that contract, while `uv.lock` captures the full resolved graph used in CI and release verification.

| Package | Version | Purpose |
| --- | --- | --- |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | `==2026.6.9` | Core video/audio download engine. Handles YouTube extraction, format selection, and downloading. |
| [yt-dlp-ejs](https://pypi.org/project/yt-dlp-ejs/) | `==0.8.0` | YouTube JavaScript solver plugin for yt-dlp. Required to bypass YouTube's bot detection. |
| [Typer](https://typer.tiangolo.com/) | `==0.25.1` | CLI framework built on Click. Defines all commands, arguments, options, and validation. |
| [Rich](https://rich.readthedocs.io/) | `==15.0.0` | Terminal formatting and display. Used for progress bars, tables (quality/language listings), colored output, and status panels. |
| [PyYAML](https://pyyaml.org/) | `==6.0.3` | YAML parsing. Used to read and write the configuration file (`~/.config/dubbed-video-downloader/config.yaml`). |
| [langcodes](https://pypi.org/project/langcodes/) | `==3.5.1` | Language tag parsing and matching. Used to resolve user-provided language names/codes against yt-dlp's audio track metadata. |

## System Dependencies

These must be installed separately on your system `PATH`. They are NOT managed by pip or pipx.

| Dependency | Minimum Version | Purpose |
| --- | --- | --- |
| [Python](https://www.python.org/) | 3.10+ | Language runtime. Required by all Python packages. |
| [Node.js](https://nodejs.org/) | recent | JavaScript runtime. Required by `yt-dlp-ejs` to execute YouTube's JavaScript challenge solver. |
| [FFmpeg](https://ffmpeg.org/) | recent | Media processing toolkit. Required by yt-dlp for merging downloaded video and audio streams into the final output file. |

### Installing System Dependencies

```bash
# Debian/Ubuntu
sudo apt install ffmpeg nodejs

# Fedora
sudo dnf install ffmpeg nodejs

# Arch
sudo pacman -S ffmpeg nodejs
```

Verify with:

```bash
ffmpeg -version
node --version
python3 --version
```

## Development Dependencies

These are installed with `uv sync --group dev`. They are only needed when contributing to the project.

### Testing

| Package | Version | Purpose |
| --- | --- | --- |
| [pytest](https://docs.pytest.org/) | `==9.1.0` | Test framework. All tests are written with pytest. |
| [pytest-cov](https://pytest-cov.readthedocs.io/) | `==7.1.0` | Coverage reporting plugin for pytest. Generates coverage reports. |
| [coverage[toml]](https://coverage.readthedocs.io/) | `==7.14.1` | Core coverage measurement library. The `[toml]` extra enables reading `[tool.coverage]` from pyproject.toml (branch coverage, 79% minimum threshold). |

### Linting and Type Checking

| Package | Version | Purpose |
| --- | --- | --- |
| [ruff](https://docs.astral.sh/ruff/) | `==0.15.17` | Fast Python linter and formatter. Replaces flake8, isort, and black. Configured with rules `E`, `F`, `I`, `UP`, `B`, `SIM`, `RUF`. |
| [mypy](https://mypy-lang.org/) | `==2.1.0` | Static type checker. Configured in strict mode (`strict = true`) targeting Python 3.10. |

### Pre-commit

| Package | Version | Purpose |
| --- | --- | --- |
| [pre-commit](https://pre-commit.com/) | `==4.6.0` | Git hook framework. Runs linting and formatting checks before each commit. |

### Type Stubs

| Package | Version | Purpose |
| --- | --- | --- |
| [types-pyyaml](https://pypi.org/project/types-PyYAML/) | `==6.0.12.20260518` | Type stubs for PyYAML, required for mypy strict mode. |
| [types-yt-dlp](https://pypi.org/project/types-yt-dlp/) | `==2026.3.17.20260605` | Type stubs for yt-dlp, required for mypy strict mode. |

## Build System

| Package | Version | Purpose |
| --- | --- | --- |
| [hatchling](https://hatch.pypa.io/) | `==1.30.1` | PEP 517 build backend. Builds the wheel from `src/dubbed_video_downloader/`. |

## Development Workflow (uv)

[uv](https://docs.astral.sh/uv/) is the package manager used for local development and CI. End users install from PyPI with pip or pipx instead. Key commands when working from a git checkout:

| Command | Purpose |
| --- | --- |
| `uv sync` | Install production dependencies into a virtual environment |
| `uv sync --group dev` | Install production + development dependencies |
| `uv run dbdvdl` | Run the CLI from source without a PyPI install |
| `uv run <command>` | Run a command inside the virtual environment (e.g., `uv run pytest`) |
| `uv run ruff check src tests` | Run the linter |
| `uv run ruff format --check src tests` | Check formatting |
| `uv run mypy` | Run the type checker |
| `uv run pytest --cov -v` | Run tests with coverage |

## Platform Support

This project is developed and tested on **Linux only**. Windows and macOS are not supported and will likely not work as expected due to path handling, subprocess differences, and reliance on Linux-native system dependencies.
