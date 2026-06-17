# Installation

## Prerequisites

Dubbed Video Downloader requires the following on your system:

| Dependency | Minimum Version | Purpose |
| --- | --- | --- |
| [Python](https://www.python.org/) | 3.10+ | Runtime |
| [Node.js](https://nodejs.org/) | recent | YouTube JavaScript solver (used by yt-dlp-ejs) |
| [FFmpeg](https://ffmpeg.org/) | recent | Media merging and processing |

**Platform note:** This project is developed and tested on **Linux only**. Windows and macOS are not supported yet and will likely not work as expected.

FFmpeg and Node.js must be available on your system `PATH`. To check:

```bash
ffmpeg -version
node --version
python3 --version
```

If FFmpeg or Node.js are not available, install them using your system's package manager:

```bash
# Debian/Ubuntu
sudo apt install ffmpeg nodejs

# Fedora
sudo dnf install ffmpeg nodejs

# Arch
sudo pacman -S ffmpeg nodejs
```

## Install from PyPI

The recommended way to install `dbdvdl` is with [pipx](https://pipx.pypa.io/), which keeps the CLI in an isolated environment:

```bash
pipx install dubbed-video-downloader
```

Alternative — install with pip into a virtual environment or with `--user`:

```bash
pip install dubbed-video-downloader
```

Verify the installation:

```bash
dbdvdl --version
dbdvdl doctor
```

`doctor` checks Python, config, FFmpeg, Node.js, and the bundled Python packages. Fix any `FAIL` results before downloading.

See [Quickstart](quickstart.md) for config setup and your first download.

## Install from Source

For contributing or running from a git checkout, clone the repository and use [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/Bedirhandd/dubbed-video-downloader.git
cd dubbed-video-downloader
uv sync
```

Run commands through uv:

```bash
uv run dbdvdl init
uv run dbdvdl doctor
```

See [CONTRIBUTING.md](https://github.com/Bedirhandd/dubbed-video-downloader/blob/main/CONTRIBUTING.md) for the full development workflow.

## Installing Dev Dependencies (for Contributors)

```bash
uv sync --group dev
```

This adds development tools: pytest, mypy, ruff, coverage[toml], pre-commit, and type stubs.

### Pre-commit Hooks

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

### Running the Test Suite

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy
uv run pytest --cov=dubbed_video_downloader --cov-report=term -v
```

The test suite is fully offline by default -- a network guard blocks TCP socket connections during test execution. To allow network access locally:

```bash
DBDVDL_TESTS_ALLOW_NETWORK=1 uv run pytest -v
```
