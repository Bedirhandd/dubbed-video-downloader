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
uv run dbdvdl qualities "https://www.youtube.com/watch?v=EXAMPLE"
uv run dbdvdl download "https://www.youtube.com/watch?v=EXAMPLE"
uv run dbdvdl download "https://www.youtube.com/watch?v=EXAMPLE" --mode audio
uv run dbdvdl download "https://www.youtube.com/watch?v=EXAMPLE" --video-quality 720p
uv run dbdvdl download "https://www.youtube.com/watch?v=EXAMPLE" --dry-run
```

Before using `langs`, `qualities`, or `download`, create the required user config:

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

To choose how existing output files are handled by default:

```bash
uv run dbdvdl init --default-exists-behavior fail
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
default_video_quality: best
default_audio_quality: best
retry_on_network_failure: 3
default_exists_behavior: skip
```

Use `ffmpeg_path: ffmpeg` to resolve FFmpeg from your system `PATH`, or set it to an absolute executable path.
Use `default_lang` as the dub language when `download` is run without `--lang`.
Use `default_download_mode` as the mode when `download` is run without
`--mode`. Supported values are `video` and `audio`.
Use `default_video_quality` for video-mode resolution selection when
`--video-quality` is omitted. Supported values are `best`, `medium`, `low`, or
an exact resolution such as `2160p`, `1080p`, or `720p`.
Use `default_audio_quality` for the selected dubbed audio stream when
`--audio-quality` is omitted. Supported values are `best`, `medium`, and `low`.
Use `retry_on_network_failure` to control how many times transient metadata,
extraction, and media download failures are retried. Set it to `0` to disable
network retries.
Use `default_exists_behavior` to control what happens when the planned output
file already exists. Supported values are `skip`, `fail`, and `overwrite`.

Inspect or remove the config with:

```bash
uv run dbdvdl config show
uv run dbdvdl config remove
```

After removing it, run `uv run dbdvdl init` again to create a fresh config.

You can pass multiple URLs and optional output/FFmpeg settings:

The CLI saves to the configured `output_dir` and uses the configured
`default_lang`, `default_download_mode`, and `default_exists_behavior`. If you
pass `--output-dir`, use an absolute path; `~` is accepted. CLI options
override config values for that run.

```bash
uv run dbdvdl download \
  "https://www.youtube.com/watch?v=EXAMPLE1" \
  "https://www.youtube.com/watch?v=EXAMPLE2" \
  --lang tr \
  --mode video \
  --video-quality 1080p \
  --audio-quality best \
  --output-dir ~/Downloads/dbdvdl-output \
  --ffmpeg-path /path/to/ffmpeg \
  --retry-on-network-failure 5 \
  --if-exists skip
```

CLI options override config values for that run, including
`--mode`, `--video-quality`, `--audio-quality`, and
`--retry-on-network-failure`, and `--if-exists`.

Existing output behavior is explicit:

```bash
uv run dbdvdl download URL --if-exists skip
uv run dbdvdl download URL --if-exists fail
uv run dbdvdl download URL --if-exists overwrite
```

- `skip` is the default and finishes successfully without downloading when the
  final output file already exists.
- `fail` stops that URL with an error when the final output file already exists.
- `overwrite` replaces the final output file using yt-dlp's overwrite behavior.

Use `qualities` to inspect the choices available for a specific URL and dub
language:

```bash
uv run dbdvdl qualities "https://www.youtube.com/watch?v=EXAMPLE" --lang tr
```

Quality behavior is intentionally strict for dubbed video output:

- Video mode selects a video-only stream and merges it with the requested
  dubbed audio stream.
- `best` uses yt-dlp's best matching video-only stream.
- Video `medium` chooses the available video-only height closest to `720p`.
- Video `low` chooses the lowest available video-only height.
- Video exact values such as `1080p` require that exact height; if unavailable,
  the command fails and prints the available heights.
- Audio `medium` chooses the selected-language audio stream closest to `128k`
  when bitrate metadata is available; otherwise it falls back to `best` with a
  note.
- Audio `low` chooses the lowest selected-language audio bitrate when metadata
  is available; otherwise it uses yt-dlp's worst matching audio selector with a
  note.

Use `--dry-run` to validate the URL, effective dub language, and effective
download mode, quality, and existing-output behavior, then print the planned
output path without downloading, merging, or creating output folders:

```bash
uv run dbdvdl download "https://www.youtube.com/watch?v=EXAMPLE" --dry-run
```

By default, yt-dlp progress, info, warnings, and debug messages are hidden to
keep CLI output focused. Use `--verbose` on `download` or `langs` to show
yt-dlp progress, info, and warnings:

```bash
uv run dbdvdl langs "https://www.youtube.com/watch?v=EXAMPLE" --verbose
uv run dbdvdl download "https://www.youtube.com/watch?v=EXAMPLE" --verbose
```

Use `--debug` for deeper troubleshooting. This enables yt-dlp debug output and
prints tracebacks for per-URL download failures:

```bash
uv run dbdvdl langs "https://www.youtube.com/watch?v=EXAMPLE" --debug
uv run dbdvdl download "https://www.youtube.com/watch?v=EXAMPLE" --debug
```

In video mode, the tool will:

1. Check if the requested dub language is available for each video.
2. Print an error with available languages if the requested language is missing.
3. Select the requested video quality and dubbed audio quality.
4. Check the planned output path against the selected `--if-exists` behavior.
5. Download the video and the requested audio stream.
6. Merge them into `.mkv`.
7. Save them under `<output-dir>/<lang>/<channel>/<title>/`.

In audio mode, the tool downloads only the selected dubbed audio stream and
saves it under the same folder structure with the native audio extension chosen
by yt-dlp. `--video-quality` is only valid in video mode.

With `--dry-run`, the tool stops after validation, output path preview, and
existing-output preview.

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

- If YouTube extraction fails or behaves unexpectedly, rerun the same `langs` or `download` command with `--verbose` to show yt-dlp progress and warnings, or `--debug` for debug logs and tracebacks.
- Output paths can be customized with `--output-dir`.

## Legal Disclaimer

- This tool is provided for **educational and personal use only**.
- Respect YouTube's [Terms of Service](https://www.youtube.com/static?template=terms) and the rights of content creators.
- Downloading and redistributing videos without permission may violate copyright laws.
