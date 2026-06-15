# Quickstart

## Create the Configuration File

Run the interactive setup wizard:

```bash
uv run dbdvdl init
```

This prompts you to configure:

- **Output directory** -- where downloads are saved (default: `~/Downloads/dbdvdl-output`)
- **FFmpeg path** -- the FFmpeg executable location (default: `ffmpeg`, found on PATH)
- **Default language** -- the dub language to use when `--lang` is omitted (default: `en`)
- **Default download mode** -- `video` or `audio` (default: `video`)
- **Default video quality** -- `best`, `medium`, `low`, or a resolution like `720p`
- **Default audio quality** -- `best`, `medium`, or `low`
- **Retry on network failure** -- how many times to retry transient failures (default: `3`)
- **Default exists behavior** -- `skip`, `fail`, or `overwrite` when output already exists
- **Ask for disk usage** -- whether to confirm downloads after showing estimated size

The config is written to `~/.config/dubbed-video-downloader/config.yaml`.

To create a config with all defaults without being prompted:

```bash
uv run dbdvdl init --default
```

To specify values directly:

```bash
uv run dbdvdl init --output-dir ~/Videos --default-lang de --default-download-mode audio
```

## Verify Your Setup

Run the doctor command to check everything:

```bash
uv run dbdvdl doctor
```

This checks:

- **Python** -- version must be 3.10+
- **Config** -- file exists and is valid at `~/.config/dubbed-video-downloader/config.yaml`
- **Output directory** -- exists or can be created, is writable
- **FFmpeg** -- executable is found and functional
- **Node.js** -- executable is found and functional
- **yt-dlp** -- package is installed
- **yt-dlp-ejs** -- package is installed

All checks should report `OK`. If any check reports `FAIL`, fix the issue before proceeding.

## First Download

### Step 1: See Available Dub Languages

```bash
uv run dbdvdl langs "https://www.youtube.com/watch?v=VIDEO_ID"
```

This lists all audio language codes available for the video. Typical output looks like:

```
en
es
fr
ja
ko
pt
```

### Step 2: Inspect Quality Options

```bash
uv run dbdvdl qualities "https://www.youtube.com/watch?v=VIDEO_ID" --lang ja
```

This shows:

- The video's title and channel
- All available languages
- All available video quality heights (e.g., `144p`, `360p`, `720p`, `1080p`)
- All available audio bitrate levels for the selected language (e.g., `128k`)

### Step 3: Download

```bash
# Download with default language and quality
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID"

# Download with a specific language and quality
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang ko --video-quality 1080p

# Download audio only
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang fr --mode audio --audio-quality medium
```
