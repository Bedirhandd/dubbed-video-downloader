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
dbdvdl init
dbdvdl doctor

# Explore a video
dbdvdl langs "https://www.youtube.com/watch?v=VIDEO_ID"
dbdvdl qualities "https://www.youtube.com/watch?v=VIDEO_ID" --lang ja

# Download
dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID"
dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang fr --video-quality 1080p
dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --mode audio --audio-quality medium
```

## Prerequisites

All examples assume you have:

1. Installed `dbdvdl` from PyPI (`pipx install dubbed-video-downloader` or `pip install dubbed-video-downloader`)
2. Run `dbdvdl init` to create the configuration file
3. Verified your setup with `dbdvdl doctor`

See [Getting Started](../getting-started/quickstart.md) for a full walkthrough.