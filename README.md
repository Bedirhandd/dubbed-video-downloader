# YouTube Dubbed Video Downloader

A Python CLI that uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [FFmpeg](https://ffmpeg.org/) to download YouTube video or audio with a specific **dub language** (for example Turkish, English, or Spanish).

This tool is helpful if you want to:

- Download YouTube videos with **dubbed audio tracks** and multi-language support.
- Save video downloads as `.mkv` files with the chosen dubbed audio merged with video.
- Save audio downloads as the selected dubbed audio stream in its native format.
- Organize downloads by **language, channel, and title**.
- Work with creators who provide **multiple audio tracks** on YouTube.

The CLI saves video-mode downloads in this folder structure:

```text
<output-dir>/<lang>/<channel>/<title>/<title>.mkv

Example:
~/Downloads/dbdvdl-output/tr/MrBeast/World_s_Deadliest_Obstacle_Course/World_s_Deadliest_Obstacle_Course.mkv
```

Audio-mode downloads use the same folder structure and keep the native audio
extension selected by yt-dlp, such as `.webm` or `.m4a`.

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
uv run dbdvdl config show
uv run dbdvdl doctor
uv run dbdvdl langs "https://www.youtube.com/watch?v=EXAMPLE"
uv run dbdvdl download "https://www.youtube.com/watch?v=EXAMPLE"
uv run dbdvdl download "https://www.youtube.com/watch?v=EXAMPLE" --mode audio
uv run dbdvdl download "https://www.youtube.com/watch?v=EXAMPLE" --dry-run
```

Before using `langs` or `download`, create the required user config:

```bash
uv run dbdvdl init
```

You can also use the equivalent config subcommand:

```bash
uv run dbdvdl config init
```

To choose a different default dub language during setup:

```bash
uv run dbdvdl init --default-lang tr
```

To choose audio-only downloads by default during setup:

```bash
uv run dbdvdl init --default-download-mode audio
```

This writes:

```text
~/.config/dubbed-video-downloader/config.yaml
```

with:

```yaml
output_dir: ~/Downloads/dbdvdl-output
ffmpeg_path: ffmpeg
default_lang: en
default_download_mode: video
retry_on_network_failure: 3
```

Use `ffmpeg_path: ffmpeg` to resolve FFmpeg from your system `PATH`, or set it to an absolute executable path.
Use `default_lang` as the dub language when `download` is run without `--lang`.
Use `default_download_mode` as the mode when `download` is run without
`--mode`. Supported values are `video` and `audio`.
Use `retry_on_network_failure` to control how many times transient metadata,
extraction, and media download failures are retried. Set it to `0` to disable
network retries.

Inspect or remove the config with:

```bash
uv run dbdvdl config show
uv run dbdvdl config remove
```

After removing it, run `uv run dbdvdl init` again to create a fresh config.

You can pass multiple URLs and optional output/FFmpeg settings:

The CLI saves to the configured `output_dir` and uses the configured
`default_lang` and `default_download_mode`. If you pass `--output-dir`, use an
absolute path; `~` is accepted. CLI options override config values for that run.

```bash
uv run dbdvdl download \
  "https://www.youtube.com/watch?v=EXAMPLE1" \
  "https://www.youtube.com/watch?v=EXAMPLE2" \
  --lang tr \
  --mode video \
  --output-dir ~/Downloads/dbdvdl-output \
  --ffmpeg-path /path/to/ffmpeg \
  --retry-on-network-failure 5
```

CLI options override config values for that run, including
`--mode` and `--retry-on-network-failure`.

Use `--dry-run` to validate the URL, effective dub language, and effective
download mode, then print the planned output path without downloading, merging,
or creating output folders:

```bash
uv run dbdvdl download "https://www.youtube.com/watch?v=EXAMPLE" --dry-run
```

By default, yt-dlp warnings and debug messages are hidden to keep CLI output
focused. Use `--verbose` on `download` or `langs` when troubleshooting:

```bash
uv run dbdvdl langs "https://www.youtube.com/watch?v=EXAMPLE" --verbose
uv run dbdvdl download "https://www.youtube.com/watch?v=EXAMPLE" --verbose
```

In video mode, the tool will:

1. Check if the requested dub language is available for each video.
2. Print an error with available languages if the requested language is missing.
3. Download the video and the requested audio stream.
4. Merge them into `.mkv`.
5. Save them under `<output-dir>/<lang>/<channel>/<title>/`.

In audio mode, the tool downloads only the selected dubbed audio stream and
saves it under the same folder structure with the native audio extension chosen
by yt-dlp.

With `--dry-run`, the tool stops after validation and output path preview.

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

- If YouTube extraction fails or behaves unexpectedly, rerun the same `langs` or `download` command with `--verbose` to show yt-dlp warnings and debug output.
- Output paths can be customized with `--output-dir`.

## Legal Disclaimer

- This tool is provided for **educational and personal use only**.
- Respect YouTube's [Terms of Service](https://www.youtube.com/static?template=terms) and the rights of content creators.
- Downloading and redistributing videos without permission may violate copyright laws.
