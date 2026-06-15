# Basic Downloads

The most common workflows for downloading dubbed videos with `dbdvdl`. Every example assumes you have completed the initial setup (`dbdvdl init` and `dbdvdl doctor`).

## Simplest Possible Download

Download a video using all defaults from your config file:

```bash
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID"
```

This uses:
- The default language from your config (e.g., `en`)
- The default download mode from your config (e.g., `video`)
- The default video and audio quality from your config (e.g., `best`)
- The default output directory from your config (e.g., `~/Downloads/dbdvdl-output`)

The file lands at `~/Downloads/dbdvdl-output/en/<channel>/<title>/<title>.mkv`.

## Specifying the Language

Pick a specific dub language with `--lang` (or `-l`):

```bash
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang ja
```

This overrides your config's `default_lang` for this single download. The output file will be placed under the `ja/` directory inside your output directory.

```bash
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang fr
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" -l de
```

## Choosing Video Quality

Set video quality with `--video-quality`. This only works with `--mode video` (the default):

```bash
# Best available resolution
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --video-quality best

# Target 720p (picks closest available height)
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --video-quality medium

# Lowest available resolution
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --video-quality low

# Exact resolution (fails if not available)
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --video-quality 1080p
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --video-quality 2160p
```

## Choosing Audio Quality

Set audio quality with `--audio-quality`. Works in both `video` and `audio` modes:

```bash
# Best available bitrate for the language
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --audio-quality best

# Target ~128 kbps (picks closest)
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --audio-quality medium

# Lowest available bitrate
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --audio-quality low
```

## Combining Language and Quality

Common combinations for different use cases:

```bash
# High quality Japanese dub
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" \
  --lang ja --video-quality 1080p

# Medium quality Korean dub
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" \
  --lang ko --video-quality medium --audio-quality medium

# Low quality German dub (conserve bandwidth)
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" \
  --lang de --video-quality low --audio-quality low
```

## Audio-Only Downloads

Download just the dubbed audio track without video:

```bash
# Best quality audio-only
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --mode audio

# Audio-only with specific language and quality
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" \
  --mode audio --lang fr --audio-quality medium
```

In audio mode:
- No video stream is downloaded
- The output keeps YouTube's native audio container (`.webm`, `.m4a`, etc.)
- `--video-quality` is not allowed -- using it produces an error

## Specifying the Output Directory

Override the config's output directory for a single run:

```bash
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" \
  --output-dir ~/Videos/dubbed

uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" \
  --output-dir /media/external-drive
```

The `--output-dir` flag supports `~` expansion and environment variable expansion. It must resolve to an absolute path -- relative paths are rejected.

## Custom FFmpeg Path

If FFmpeg is installed at a non-standard location:

```bash
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" \
  --ffmpeg-path /usr/local/bin/ffmpeg
```

Use `--ffmpeg-path ffmpeg` (the default) to find FFmpeg on the system PATH.

## Previewing Before Downloading (Dry Run)

Use `--dry-run` to validate everything without actually downloading:

```bash
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --dry-run
```

Expected output:

```
Dry run: no files will be downloaded or created.
Title: Example Video Title
Channel: ChannelName
Language: en
Mode: video
Video quality: best
Audio quality: best
Available languages: en, es, fr, ja, ko
Output: ~/Downloads/dbdvdl-output/en/ChannelName/Example Video Title/Example Video Title.mkv
Estimated disk usage: ~250 MB
If output exists: skip
Output exists: no
Dry run OK
```

A dry run:
- Fetches metadata from YouTube
- Resolves the language against available tracks
- Shows the planned output path
- Estimates disk usage (when format metadata provides filesize)
- Reports whether the output file already exists
- Shows what would happen based on your `--if-exists` setting
- Does **not** download any media

## Handling Existing Files

Control what happens when the output file already exists:

```bash
# Skip if file exists (default behavior)
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --if-exists skip

# Fail with an error if file exists
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --if-exists fail

# Overwrite the existing file
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --if-exists overwrite
```

When `skip` is used and the file exists, the output shows `Skipped` and the existing file path.

## Working with Disk Usage Prompts

If your config has `ask_for_disk_usage: true`, downloads will prompt for confirmation:

```bash
# Approve all prompts for this run
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --yes

# Same but shorter
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" -y
```

## Verbose and Debug Output

When a download fails or you need to see what's happening:

```bash
# Show yt-dlp progress and warnings
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --verbose

# Show yt-dlp debug output and full error tracebacks
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --debug
```

With `--verbose`, you see yt-dlp's own progress bar instead of the minimal status display. With `--debug`, you get the maximum detail level including yt-dlp's debug log and, on failure, the full Python traceback sent to stderr.

## Network Retry Control

Adjust how many times network failures are retried:

```bash
# No retries (fail immediately on network errors)
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" \
  --retry-on-network-failure 0

# More retries for unreliable connections
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" \
  --retry-on-network-failure 5
```

Retries use exponential backoff: the delay doubles each attempt (1s, 2s, 4s, 8s maximum) with a random jitter of up to 1 second. Retries apply to metadata extraction, media downloads, and fragment downloads.

## Complete Example: Download with Everything Specified

```bash
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" \
  --lang tr \
  --mode video \
  --video-quality 720p \
  --audio-quality medium \
  --output-dir ~/Videos/dubbed \
  --if-exists overwrite \
  --retry-on-network-failure 5 \
  --yes \
  --verbose
```

This command:
- Downloads a Turkish dub (`--lang tr`)
- In video mode (downloads both video and audio, merges into MKV)
- At 720p video quality
- With medium audio bitrate (~128 kbps)
- Saves to `~/Videos/dubbed/tr/<channel>/<title>/<title>.mkv`
- Overwrites if the file already exists
- Retries network failures up to 5 times
- Auto-approves any disk usage prompts
- Shows verbose yt-dlp output

## Next Steps

- [Language and Dubs](language-and-dubs.md) -- Listing languages, region variants, fallback behavior
- [Quality and Format](quality-and-format.md) -- Resolution presets, audio bitrate tiers, inspecting options
- [Batch and Multiple URLs](batch-and-playlists.md) -- Downloading multiple videos at once
