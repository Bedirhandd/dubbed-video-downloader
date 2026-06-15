# Quality and Format

Examples focused on video resolution selection, audio bitrate tiers, and inspecting available quality options before downloading.

## Quality Presets Overview

`dbdvdl` uses three quality tiers for both video and audio:

| Tier | Video Behavior | Audio Behavior |
| --- | --- | --- |
| `best` | Highest available resolution | Highest available bitrate |
| `medium` | Closest to 720p | Closest to ~128 kbps |
| `low` | Lowest available resolution | Lowest available bitrate |

Additionally, video quality supports exact resolution targets (e.g., `1080p`, `2160p`).

## Inspecting Available Qualities

Before choosing a quality, inspect what the video offers:

```bash
uv run dbdvdl qualities "https://www.youtube.com/watch?v=VIDEO_ID" --lang fr
```

Expected output (example):

```
Title: Example Video Title
Channel: ChannelName
Language: fr
Available languages: en, fr, ja
Video qualities: 144p, 360p, 720p, 1080p, 2160p
Audio qualities: 128k, 256k
```

This tells you:
- **Video qualities:** Every available resolution height
- **Audio qualities:** Every available bitrate for the language's dubbed audio, including streams with unknown bitrate flagged separately

## Video Quality: Best

Download at the highest available resolution:

```bash
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --video-quality best
```

This selects `bv` (best video-only stream). It always succeeds as long as the video has any video stream.

## Video Quality: Medium

Target approximately 720p. The system picks the closest available height:

```bash
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --video-quality medium
```

Behavior by available heights:
- Heights `[360p, 720p, 1080p]` → selects `720p` (exact match)
- Heights `[480p, 1080p]` → selects `480p` (closer to 720 than 1080)
- Heights `[1080p, 2160p]` → selects `1080p` (closest to 720)
- When two heights are equidistant, the lower one is chosen

## Video Quality: Low

Download at the lowest available resolution:

```bash
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --video-quality low
```

This picks the smallest height from the available list.

## Video Quality: Exact Resolution

Request a specific resolution. The command fails if that exact height is not available:

```bash
# Succeeds if 1080p is listed in qualities output
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --video-quality 1080p

# Succeeds if 2160p (4K) is available
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --video-quality 2160p

# Fails if 480p is not among the available heights
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --video-quality 480p
```

Error when the resolution is unavailable:

```
Input error: Requested video quality 480p is not available. Available video qualities: 144p, 360p, 720p, 1080p.
```

Valid resolution range: `144p` through `8640p`.

## Audio Quality: Best

Download at the highest available bitrate for the selected language:

```bash
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --audio-quality best
```

When every candidate for the language reports bitrate metadata, the system picks the highest-bitrate audio candidate and builds a targeted yt-dlp selector (typically `bestaudio[format_id="…"]`). When any candidate lacks bitrate metadata, `best` falls back to yt-dlp's `bestaudio[language="<lang>"]` filter so unknown streams stay in contention. When no candidate reports bitrate metadata, it uses the same language-based fallback.

In video mode, the audio selector is combined with the video selector using `+`.

## Audio Quality: Medium

Target approximately 128 kbps. The system picks the audio candidate closest to 128k:

```bash
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --audio-quality medium
```

Selection logic:
- Candidates at `[64k, 128k, 256k]` → selects `128k` (exact match)
- Candidates at `[64k, 256k]` → selects `64k` (closer to 128, exact tie broken by lower bitrate)
- If no candidates have bitrate metadata → falls back to `best` with a note

When bitrate metadata is unavailable:

```
Note: Audio quality medium fell back to best because bitrate metadata is unavailable.
```

## Audio Quality: Low

Download at the lowest available bitrate:

```bash
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --audio-quality low
```

If no candidates have bitrate metadata, falls back to yt-dlp's `worstaudio` filter for the language:

```
Note: Audio quality low is using yt-dlp's worst matching audio because bitrate metadata is unavailable.
```

## Combined Quality Selection

Specify both video and audio quality together:

```bash
# 1080p video, best audio
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" \
  --video-quality 1080p --audio-quality best

# Medium video (target 720p), low audio (conserve bandwidth)
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" \
  --video-quality medium --audio-quality low
```

## Audio-Only Quality Selection

In audio mode, `--video-quality` is not allowed:

```bash
# This works
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" \
  --mode audio --audio-quality medium

# This produces an error
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" \
  --mode audio --video-quality 1080p
```

Error output:

```
Input error: --video-quality can only be used with --mode video.
```

## Understanding Quality in Dry Runs

A dry run shows your requested quality and what was actually selected:

```bash
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" \
  --video-quality medium --dry-run
```

Partial output:

```
Video quality: medium (selected 720p)
Audio quality: best
```

When the selected quality differs from the requested quality, both are shown:
- `medium` is what you asked for
- `(selected 720p)` is what the system resolved to

If they match exactly (e.g., `best` → `best`), only one value is shown:

```
Video quality: best
```

## Quality in Output Paths

Quality selection affects the selected format streams but does **not** change the output path. The file always lands at:

```
output_dir/<language>/<channel>/<title>/<title>.<ext>
```

Downloading the same video twice with different quality settings (and `--if-exists overwrite`) will overwrite the previous file.

## Understanding Audio Quality Candidates

The `qualities` command shows audio bitrate information per language. When no bitrate is available for some streams:

```
Audio qualities: 128k, 256k, unknown bitrate (2 streams)
```

This means some audio streams for the language are missing bitrate metadata. The quality system handles this gracefully:
- `best` uses yt-dlp's `bestaudio[language="<lang>"]` when any stream lacks bitrate metadata, or when no stream reports bitrate metadata
- `medium` falls back to `best` with a note when no stream reports bitrate metadata
- `low` falls back to `worstaudio` with a note when no stream reports bitrate metadata

## Video Quality Validation Errors

Invalid quality values produce an immediate error:

```bash
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --video-quality ultra
```

Error output:

```
Input error: video_quality must be `best`, `medium`, `low`, or a video resolution from 144p through 8640p.
```

Resolution outside the valid range:

```bash
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --video-quality 100p
```

Error output:

```
Input error: video_quality must be between 144p and 8640p.
```

## Next Steps

- [Language and Dubs](language-and-dubs.md) -- Language selection and resolution
- [Configuration](configuration.md) -- Setting default qualities in config
- [Basic Downloads](basic-downloads.md) -- Simple download workflows
