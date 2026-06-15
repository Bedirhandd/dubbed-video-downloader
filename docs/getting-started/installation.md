# Installation

## Prerequisites

Dubbed Video Downloader requires the following to be installed on your system:

| Dependency | Minimum Version | Purpose |
| --- | --- | --- |
| [Python](https://www.python.org/) | 3.10+ | Runtime |
| [uv](https://docs.astral.sh/uv/) | recent | Package manager and virtual environment |
| [Node.js](https://nodejs.org/) | recent | YouTube JavaScript solver (used by yt-dlp-ejs) |
| [FFmpeg](https://ffmpeg.org/) | recent | Media merging and processing |

**Platform note:** This project is developed and tested on **Linux only**. Windows and macOS are not supported yet and will likely not work as expected.

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/Bedirhandd/dubbed-video-downloader.git
cd dubbed-video-downloader
```

### 2. Install Dependencies

```bash
uv sync
```

This installs the production dependencies (yt-dlp, yt-dlp-ejs, Typer, Rich, PyYAML, langcodes) into a virtual environment managed by uv.

### 3. Verify Prerequisites

FFmpeg and Node.js must be available on your system `PATH`. To check:

```bash
ffmpeg -version
node --version
```

If they are not available, install them using your system's package manager:

```bash
# Debian/Ubuntu
sudo apt install ffmpeg nodejs

# Fedora
sudo dnf install ffmpeg nodejs

# Arch
sudo pacman -S ffmpeg nodejs
```

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
