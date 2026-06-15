# Usage Examples

Practical, copy-pasteable examples covering common workflows with Dubbed Video Downloader (`dbdvdl`). Every command shown here has been verified against the actual CLI interface.

## Example Categories

| Document | Description |
| --- | --- |
| [Basic Downloads](basic-downloads.md) | Single video downloads, output paths, quality and language selection. The most common workflows for new users. |
| [Language and Dubs](language-and-dubs.md) | Listing languages, selecting specific dubs, language fallback behavior, region-variant codes. |
| [Quality and Format](quality-and-format.md) | Resolution selection, audio bitrate tiers, format inspection, quality fallback notes. |
| [Configuration](configuration.md) | Setting up config, showing/removing config, CLI overrides, re-initializing with different defaults. |
| [Batch and Multiple URLs](batch-and-playlists.md) | Downloading multiple videos in a single command, handling failures across URLs. |
| [Troubleshooting](troubleshooting.md) | Common errors and their resolutions, debug logging, environment verification, interrupted downloads. |

## Quick Reference

```bash
# Setup (one-time)
uv run dbdvdl init
uv run dbdvdl doctor

# Explore a video
uv run dbdvdl langs "https://www.youtube.com/watch?v=VIDEO_ID"
uv run dbdvdl qualities "https://www.youtube.com/watch?v=VIDEO_ID" --lang ja

# Download
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID"
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang fr --video-quality 1080p
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --mode audio --audio-quality medium
```

## Prerequisites

All examples assume you have:

1. Cloned the repository and installed dependencies with `uv sync`
2. Run `uv run dbdvdl init` to create the configuration file
3. Verified your setup with `uv run dbdvdl doctor`

See [Getting Started](../getting-started/quickstart.md) for a full walkthrough.