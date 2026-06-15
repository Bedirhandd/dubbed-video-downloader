# Language and Dubs

Examples focused on language selection, listing available dubs, language fallback behavior, and downloading multiple language tracks.

## Listing Available Languages

Before downloading, inspect what dub languages a video offers:

```bash
uv run dbdvdl langs "https://www.youtube.com/watch?v=VIDEO_ID"
```

Expected output (example):

```
en
es-419
fr
ja
ko
pt-BR
```

Each line is a BCP-47 language tag found in the video's audio format metadata. Invalid or undefined tags are skipped with a warning.

### With Network Retry Control

```bash
uv run dbdvdl langs "https://www.youtube.com/watch?v=VIDEO_ID" --retry-on-network-failure 5
```

### With Verbose Output

```bash
uv run dbdvdl langs "https://www.youtube.com/watch?v=VIDEO_ID" --verbose
```

### When No Valid Languages Exist

If the video has audio tracks but none with valid language tags:

```
Audio tracks were found but none have a valid language tag (skipped: und, und).
```

If the video has no multi-language audio tracks at all:

```
No multi-language audio tracks found.
```

## Simple Language Selection

Download with a specific dub language:

```bash
# Two-letter code
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang ja

# Three-letter code (ISO 639-3)
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang jpn

# Region-variant code
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang pt-BR
```

## Language Code Formats

All language codes are validated and normalized using the `langcodes` library. Supported input formats:

| Format | Example | Notes |
| --- | --- | --- |
| Two-letter | `en`, `ja`, `ko`, `tr`, `es`, `fr`, `de` | Most common format. ISO 639-1. |
| Three-letter | `eng`, `jpn`, `kor`, `tur` | ISO 639-3. Normalized to standard form on save. |
| With region | `en-US`, `pt-BR`, `es-MX` | Triggers exact match only. |
| With script | `zh-Hans`, `zh-Hant` | Triggers exact match only. |

During config initialization, codes are normalized: for example, entering `tur` becomes `tr` in the config file.

## Language Fallback Behavior

When you request a language, the system performs a multi-step resolution:

### Step 1: Exact Match

The canonical BCP-47 code is matched case-insensitively against the raw metadata tags. For example, requesting `en` matches both `en` and `en-US` in the video's metadata:

```bash
# If the video has tracks tagged "en" and "en-US", requesting "en" matches "en"
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang en
```

### Step 2: Fuzzy Match

If no exact match exists and you did not specify a territory or script, the system uses `langcodes.closest_supported_match()` to find a related language:

```bash
# If the video has "es-419" (Latin American Spanish) but no plain "es",
# requesting "es" will still match via fuzzy resolution
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang es
```

The output shows the resolved language:

```
Language: es (track: es-419)
```

### Step 3: Error

If no match is found:

```bash
# If the video only has "en" and "ja", this fails
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang fr
```

Error output:

```
Error: Requested dub language not found.
Requested: fr
Available: en, ja
```

## Region and Script Variants (Exact Match Only)

If your language code includes a region or script qualifier, only an exact match is accepted. No fuzzy matching occurs:

```bash
# Only matches a track explicitly tagged "pt-BR" — does not match plain "pt"
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang pt-BR

# Only matches "zh-Hans" — does not match "zh" or "zh-Hant"
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang zh-Hans
```

## Downloading Different Languages of the Same Video

Download multiple language tracks of the same video with separate commands:

```bash
# Download Japanese dub
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang ja

# Download Korean dub (goes into a separate directory)
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang ko

# Download French audio-only
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang fr --mode audio
```

Each language produces a separate output path under the `output_dir`:

```
~/Downloads/dbdvdl-output/ja/<channel>/<title>/<title>.mkv
~/Downloads/dbdvdl-output/ko/<channel>/<title>/<title>.mkv
~/Downloads/dbdvdl-output/fr/<channel>/<title>/<title>.webm
```

## Inspecting Quality Options for a Language

Use `qualities` to see what quality options exist before downloading:

```bash
uv run dbdvdl qualities "https://www.youtube.com/watch?v=VIDEO_ID" --lang ja
```

Expected output (example):

```
Title: Example Video
Channel: ChannelName
Language: ja
Available languages: en, ja, ko, pt-BR
Video qualities: 144p, 360p, 720p, 1080p, 2160p
Audio qualities: 128k, 256k
```

The `qualities` command uses the same language resolution as `download`. You can set the language explicitly or let it fall back to your config's `default_lang`:

```bash
# Uses config default_lang
uv run dbdvdl qualities "https://www.youtube.com/watch?v=VIDEO_ID"

# Explicit language
uv run dbdvdl qualities "https://www.youtube.com/watch?v=VIDEO_ID" --lang ko
```

## Handling Skipped Invalid Tracks

When YouTube provides audio tracks with missing, empty, or invalid language metadata, the system warns about them but continues:

```bash
uv run dbdvdl langs "https://www.youtube.com/watch?v=VIDEO_ID"
```

If tracks were skipped:

```
en
ja
Skipped 2 audio track(s) with invalid or undefined language metadata.
```

During downloads, the `skipped_invalid_count` is also shown in dry-run output:

```
Dry run: no files will be downloaded or created.
...
Available languages: en, ja, ko
```

## Error: Invalid Language Code

Using an invalid language code produces an immediate error before any network request:

```bash
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang invalid!
```

Error output:

```
Input error: --lang is not a valid language code: 'invalid!'.
```

## Setting a Different Default Language

Change the default language in your config:

```bash
# Interactive re-initialization
uv run dbdvdl init --force --default-lang ja

# Non-interactive with all defaults preserved and only language changed
uv run dbdvdl init --force --default --default-lang ko
```

Verify the change:

```bash
uv run dbdvdl config show
```

Partial output:

```
Default language: ko
```

## Next Steps

- [Quality and Format](quality-and-format.md) -- Resolution presets, audio bitrate tiers
- [Basic Downloads](basic-downloads.md) -- Simple download workflows
- [Configuration](configuration.md) -- Setting and managing config defaults
