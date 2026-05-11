# YouTube Dubbed Video Downloader

A Python CLI that uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [FFmpeg](https://ffmpeg.org/) to download YouTube videos with a specific **dub language** (for example Turkish, English, or Spanish).

This tool is helpful if you want to:

- Download YouTube videos with **dubbed audio tracks** and multi-language support.
- Save the output as `.mkv` files with the chosen dubbed audio merged with video.
- Organize downloaded videos by **language, channel, and title**.
- Work with creators who provide **multiple audio tracks** on YouTube.

The CLI saves videos in this folder structure:

```text
<output-dir>/<lang>/<channel>/<title>/<title>.mkv

Example:
~/Downloads/dbdvdl-output/tr/MrBeast/World_s_Deadliest_Obstacle_Course/World_s_Deadliest_Obstacle_Course.mkv
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
- **FFmpeg** installed and accessible in your system `PATH`, or set in the config file

Check if Node.js and FFmpeg are available:

```bash
node --version
ffmpeg -version
```

If FFmpeg is not installed, download it from the official site: [https://ffmpeg.org/](https://ffmpeg.org/)

## Installation

Clone the repo, then install uv if needed:

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

## Usage

Use the CLI with uv:

```bash
uv run dbdvdl --help
uv run dbdvdl init
uv run dbdvdl doctor
uv run dbdvdl langs "https://www.youtube.com/watch?v=EXAMPLE"
uv run dbdvdl download "https://www.youtube.com/watch?v=EXAMPLE" --lang tr
```

Before using `langs` or `download`, create the required user config:

```bash
uv run dbdvdl init
```

This writes:

```text
~/.config/dubbed-video-downloader/config.yaml
```

with:

```yaml
output_dir: ~/Downloads/dbdvdl-output
ffmpeg_path: ffmpeg
```

Use `ffmpeg_path: ffmpeg` to resolve FFmpeg from your system `PATH`, or set it to an absolute executable path.

You can pass multiple URLs and optional output/FFmpeg settings:

The CLI saves to the configured `output_dir`. If you pass `--output-dir`, use an
absolute path; `~` is accepted. CLI options override config values for that run.

```bash
uv run dbdvdl download \
  "https://www.youtube.com/watch?v=EXAMPLE1" \
  "https://www.youtube.com/watch?v=EXAMPLE2" \
  --lang en \
  --output-dir ~/Downloads/dbdvdl-output \
  --ffmpeg-path /path/to/ffmpeg
```

The tool will:

1. Check if the requested dub language is available for each video.
2. Print an error with available languages if the requested language is missing.
3. Download the video and the requested audio stream.
4. Merge them into `.mkv`.
5. Save them under `<output-dir>/<lang>/<channel>/<title>/`.

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

- If the CLI prints warnings like `WARNING: Unable to download format 616. Skipping...`, this is normal. yt-dlp tries multiple format IDs, and some may be unavailable. It automatically falls back to a working format.
- Output paths can be customized with `--output-dir`.

## Legal Disclaimer

- This tool is provided for **educational and personal use only**.
- Respect YouTube's [Terms of Service](https://www.youtube.com/static?template=terms) and the rights of content creators.
- Downloading and redistributing videos without permission may violate copyright laws.
