# Config Keys Reference

## `output_dir`

| Property | Value |
| --- | --- |
| **Type** | `str` |
| **Required** | Yes |
| **Default** | `~/Downloads/dbdvdl-output` |
| **CLI override** | `--output-dir` / `-o` on the `download` command |

Absolute directory where all downloads are saved. Supports:
- `~` expansion (e.g., `~/Videos`)
- Environment variable expansion (e.g., `$HOME/Videos`)

Must resolve to an absolute path. Relative paths are rejected.

The output layout within this directory is always `language / channel / title / title.ext`.

## `ffmpeg_path`

| Property | Value |
| --- | --- |
| **Type** | `str` |
| **Required** | Yes |
| **Default** | `ffmpeg` |
| **CLI override** | `--ffmpeg-path` on the `download` command |

Path to the FFmpeg executable. Valid values:
- `ffmpeg` or `ffmpeg.exe` -- look up on system PATH at runtime
- An absolute path (e.g., `/usr/local/bin/ffmpeg`)

When set to `ffmpeg`, yt-dlp is not explicitly told where FFmpeg is -- it finds the executable on the system PATH. When set to an absolute path, yt-dlp is configured to use that specific binary.

## `default_lang`

| Property | Value |
| --- | --- |
| **Type** | `str` |
| **Required** | Yes |
| **Default** | `en` |
| **CLI override** | `--lang` / `-l` on the `download` and `qualities` commands |

The dub language code to use when `--lang` is omitted. Must be a valid BCP-47 language code. Supported formats:
- Two-letter codes: `en`, `ja`, `ko`, `tr`, `es`, `fr`, `de`
- Three-letter codes: `eng`, `jpn`, `kor`
- Codes with region/script: `en-US`, `zh-Hans`

The value is normalized using `langcodes` during config write: aliases are converted to their standard form (e.g., `tur` becomes `tr`).

## `default_download_mode`

| Property | Value |
| --- | --- |
| **Type** | `str` |
| **Required** | No (defaults to `video`) |
| **Default** | `video` |
| **CLI override** | `--mode` on the `download` command |

The download mode to use when `--mode` is omitted. Valid values:
- `video` -- download video with dubbed audio track merged into MKV
- `audio` -- download only the dubbed audio stream in native format

## `default_video_quality`

| Property | Value |
| --- | --- |
| **Type** | `str` |
| **Required** | No (defaults to `best`) |
| **Default** | `best` |
| **CLI override** | `--video-quality` on the `download` command |

The video quality to use for video-mode downloads when `--video-quality` is omitted. Valid values:

| Value | Behavior |
| --- | --- |
| `best` | Select the highest available video quality. |
| `medium` | Target 720p. Picks the closest available height to 720p. |
| `low` | Select the lowest available video quality. |
| `Np` | Exact resolution in pixels, from `144p` through `8640p`. Fails if the exact resolution is not available. Examples: `360p`, `720p`, `1080p`, `2160p`. |

## `default_audio_quality`

| Property | Value |
| --- | --- |
| **Type** | `str` |
| **Required** | No (defaults to `best`) |
| **Default** | `best` |
| **CLI override** | `--audio-quality` on the `download` command |

The dubbed audio quality to use when `--audio-quality` is omitted. Valid values:

| Value | Behavior |
| --- | --- |
| `best` | Select the highest available audio bitrate for the target language. |
| `medium` | Target approximately 128 kbps. Picks the candidate closest to 128k. Falls back to `best` if bitrate metadata is unavailable. |
| `low` | Select the lowest available audio bitrate for the target language. |

## `retry_on_network_failure`

| Property | Value |
| --- | --- |
| **Type** | `int` |
| **Required** | No (defaults to `3`) |
| **Default** | `3` |
| **CLI override** | `--retry-on-network-failure` on `download`, `langs`, and `qualities` |

How many times to retry transient network failures during metadata extraction, media download, and other HTTP requests. Applied to yt-dlp's `retries`, `fragment_retries`, and `extractor_retries` settings.

Must be a non-negative integer. `0` disables retries entirely. Maximum retry sleep is capped at 8 seconds with exponential backoff (2^n seconds plus a random jitter of up to 1 second).

## `default_exists_behavior`

| Property | Value |
| --- | --- |
| **Type** | `str` |
| **Required** | No (defaults to `skip`) |
| **Default** | `skip` |
| **CLI override** | `--if-exists` on the `download` command |

What to do when the planned output file already exists. Valid values:

| Value | Behavior |
| --- | --- |
| `skip` | Silently skip the download. Return status `SKIPPED`. |
| `fail` | Raise an error (`DownloadError`). Download is not attempted. |
| `overwrite` | Replace the existing file with the new download. |

## `ask_for_disk_usage`

| Property | Value |
| --- | --- |
| **Type** | `bool` |
| **Required** | No (defaults to `false`) |
| **Default** | `false` |
| **CLI override** | `--yes` / `-y` (approves the prompt without asking) |

When set to `true`, each download will display an estimated disk usage and ask for confirmation before proceeding. When `false`, downloads proceed without disk usage confirmation.

In non-interactive environments (stdin is not a TTY), if this is `true` and `--yes` is not used, the command refuses to run and exits with an error.
