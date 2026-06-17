# `dbdvdl download`

**Description:** Download one or more YouTube videos with a selected dubbed audio track. Videos are downloaded in `mkv` format (video mode) or native format (audio mode) into `output_dir / language / channel / title /`.

**Usage:**

```
uv run dbdvdl download [OPTIONS] URL...
```

## Arguments

| Name | Required | Description |
| --- | --- | --- |
| `URL...` | Yes (at least one) | One or more YouTube video URLs to download. Each URL must use `http` or `https` and include a host. Multiple URLs are downloaded sequentially. |

## Options

### `--lang`, `-l`

| Property | Value |
| --- | --- |
| Type | `str` |
| Default | Config default (`default_lang`) |
| Description | Target dub language code. Overrides the config default. Must be a valid BCP-47 language code (e.g., `en`, `ja`, `ko`, `tr`). |

### `--mode`

| Property | Value |
| --- | --- |
| Type | `video` \| `audio` |
| Default | Config default (`default_download_mode`) |
| Description | Download mode. `video` downloads both video and the selected dubbed audio, merged into an MKV. `audio` downloads only the dubbed audio stream. |

### `--output-dir`, `-o`

| Property | Value |
| --- | --- |
| Type | `str` |
| Default | Config default (`output_dir`) |
| Description | Absolute directory where downloads will be saved. Supports `~` expansion and environment variable expansion. |

### `--ffmpeg-path`

| Property | Value |
| --- | --- |
| Type | `str` |
| Default | Config default (`ffmpeg_path`) |
| Description | Path to the FFmpeg executable. Use `ffmpeg` to rely on the system PATH. Override this if FFmpeg is installed at a custom location. Before metadata or download work starts, `download` rejects missing or non-executable paths using the same resolution messages as `dbdvdl doctor` (for example, `ffmpeg was not found on PATH` or `{path} does not exist`). |

### `--video-quality`

| Property | Value |
| --- | --- |
| Type | `str` |
| Default | Config default (`default_video_quality`) |
| Description | Video quality for video mode. Valid values: `best` (highest available), `medium` (targets 720p, picks closest), `low` (lowest available), or an exact resolution like `1080p` (from `144p` through `8640p`). Can only be used with `--mode video`. |

### `--audio-quality`

| Property | Value |
| --- | --- |
| Type | `str` |
| Default | Config default (`default_audio_quality`) |
| Description | Dubbed audio quality. Valid values: `best` (highest bitrate), `medium` (targets ~128kbps), `low` (lowest bitrate). |

### `--dry-run`

| Property | Value |
| --- | --- |
| Type | `bool` |
| Default | `False` |
| Description | Validate metadata and print the planned output and estimated disk usage without actually downloading. Shows title, channel, language, mode, qualities, output path, estimated size, and what would happen if the output already exists. |

### `--verbose`, `-v`

| Property | Value |
| --- | --- |
| Type | `bool` |
| Default | `False` |
| Description | Show yt-dlp download progress, info messages, and warnings. When not set (default), yt-dlp output is suppressed and a minimal status display is shown instead. |

### `--debug`

| Property | Value |
| --- | --- |
| Type | `bool` |
| Default | `False` |
| Description | Show yt-dlp debug output and full Python error tracebacks on failure. Useful for diagnosing download issues. |

### `--retry-on-network-failure`

| Property | Value |
| --- | --- |
| Type | `int` |
| Default | Config default (default: `3`) |
| Description | Network retries for metadata, extraction, and media downloads. Overrides the config value. Must be a non-negative integer. `0` disables retries. |

### `--if-exists`

| Property | Value |
| --- | --- |
| Type | `skip` \| `fail` \| `overwrite` |
| Default | Config default (`default_exists_behavior`) |
| Description | Behavior when the planned output file already exists. `skip` silently skips the download, `fail` raises an error, `overwrite` replaces the existing file. |

### `--yes`, `-y`

| Property | Value |
| --- | --- |
| Type | `bool` |
| Default | `False` |
| Description | Automatically approve disk usage confirmation prompts for this download run. Useful for scripting or when you do not want to be prompted. Also used to allow non-interactive downloads when disk usage confirmation is enabled in config. |

## Examples

```bash
# Download with default settings
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID"

# Download multiple videos
uv run dbdvdl download "https://www.youtube.com/watch?v=ID1" "https://www.youtube.com/watch?v=ID2"

# Download with Japanese dub at 1080p
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang ja --video-quality 1080p

# Audio-only download in French, medium quality
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang fr --mode audio --audio-quality medium

# Preview what would be downloaded
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --dry-run

# Overwrite existing files, auto-approve disk usage prompts, verbose output
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --if-exists overwrite --yes --verbose

# Debug a failing download
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --debug

# Custom output directory and FFmpeg path
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --output-dir /media/external --ffmpeg-path /usr/local/bin/ffmpeg
```

## Download Status Display

By default (when not using `--verbose`, `--debug`, or `--dry-run` and running in an interactive terminal), the command shows a brief status message per download stage:

```
[done] Checking configuration...
[done] Preparing options...
[done] Fetching metadata...
[done] Checking available languages...
[done] Selecting qualities...
[done] Planning output path...
[done] Preparing output directory...
[done] Downloading media...
[done] Merging media...
[done] Finalizing output...
```

During the download phase, progress is updated approximately every 250ms showing speed, ETA, and percentage completed.
