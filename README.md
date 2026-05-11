# YouTube Dubbed Video Downloader

A simple Python script that uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [FFmpeg](https://ffmpeg.org/) to download YouTube videos with a specific **dub language** (for example Turkish, English, or Spanish).

This tool is helpful if you want to:

- Download YouTube videos with **dubbed audio tracks** and multi-language support.
- Save the output as `.mkv` files with the chosen dubbed audio merged with video.
- Organize downloaded videos by **language, channel, and title**.
- Work with creators who provide **multiple audio tracks** on YouTube.

The script saves videos in this folder structure:

```text
Videos/<lang>/<channel>/<title>/<title>.mkv

Example:
Videos/tr/MrBeast/World_s_Deadliest_Obstacle_Course/World_s_Deadliest_Obstacle_Course.mkv
```

## Tested Environment

- Python `3.12.3`
- `yt-dlp==2026.3.17`
- `yt-dlp-ejs==0.8.0`
- Node.js `22.22.2`
- Dependency management with [uv](https://docs.astral.sh/uv/)

## Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Python `>=3.10` (uv can use the project `.python-version`)
- Node.js on your system `PATH` for yt-dlp's YouTube JavaScript challenge solver
- **FFmpeg** installed and accessible in your system `PATH`, or set with `FFMPEG_PATH` in the script

Check if Node.js and FFmpeg are available:

```bash
node --version
ffmpeg -version
```

If FFmpeg is not installed, download it from the official site: [https://ffmpeg.org/](https://ffmpeg.org/)

## Installation

Clone the repo or copy the script file, then install uv if needed:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows PowerShell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Sync the project environment:

```bash
uv sync
```

uv will create `.venv/` and install the dependencies from `pyproject.toml` and `uv.lock`.
The project includes `yt-dlp-ejs`; Node.js is still needed to run the solver for full YouTube format and dubbed-audio discovery.

## Configuration

The CLI does not require editing files. Pass options such as `--lang`, `--output-dir`, and `--ffmpeg-path` at runtime.

For legacy script usage, open `script.py` and edit these lines if needed:

```python
DUB_LANGUAGE = "tr"   # Target dub language, e.g. "tr", "en"
FFMPEG_PATH = None    # Example: "C:/ffmpeg/ffmpeg.exe"
                      # Leave as None to let yt-dlp find FFmpeg in PATH
VIDEO_URLS = [
    "https://www.youtube.com/watch?v=EXAMPLE1",
    "https://www.youtube.com/watch?v=EXAMPLE2",
]
```

- `DUB_LANGUAGE`: set the language code you want (`"tr"`, `"en"`, etc.).
- `FFMPEG_PATH`: if FFmpeg is not in your system `PATH`, put its full path here.
- `VIDEO_URLS`: add the video URLs you want to download.

## Usage

Use the CLI with uv:

```bash
uv run dbdvdl --help
uv run dbdvdl --doctor
uv run dbdvdl langs "https://www.youtube.com/watch?v=EXAMPLE"
uv run dbdvdl download "https://www.youtube.com/watch?v=EXAMPLE" --lang tr
```

You can pass multiple URLs and optional output/FFmpeg settings:

```bash
uv run dbdvdl download \
  "https://www.youtube.com/watch?v=EXAMPLE1" \
  "https://www.youtube.com/watch?v=EXAMPLE2" \
  --lang en \
  --output-dir Videos \
  --ffmpeg-path /path/to/ffmpeg
```

The legacy script entrypoint is still available:

```bash
uv run script.py
```

The tool will:

1. Check if the requested dub language is available for each video.
2. Print an error with available languages if the requested language is missing.
3. Download the video and the requested audio stream.
4. Merge them into `.mkv`.
5. Save them under `Videos/<lang>/<channel>/<title>/`.

## Updating Dependencies

To upgrade yt-dlp within the uv-managed project:

```bash
uv lock --upgrade-package yt-dlp
uv lock --upgrade-package yt-dlp-ejs
uv sync
```

Commit the updated `uv.lock` when dependency versions change. Do not edit `uv.lock` manually.

## Contributing

Contributions and issues are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for commit, branch, and pull request guidelines.

## Notes

- If the script prints warnings like `WARNING: Unable to download format 616. Skipping...`, this is normal. yt-dlp tries multiple format IDs, and some may be unavailable. It automatically falls back to a working format.
- Output paths can be customized by editing the `outtmpl()` function in the script.

## Legal Disclaimer

- This script is provided for **educational and personal use only**.
- Respect YouTube's [Terms of Service](https://www.youtube.com/static?template=terms) and the rights of content creators.
- Downloading and redistributing videos without permission may violate copyright laws.
