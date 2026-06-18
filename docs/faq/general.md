# General FAQ

## What does this tool do?

It downloads YouTube videos or audio tracks with a specific dubbed (multi-language) audio track. If a video has audio in English, Japanese, French, and Korean, you can pick which dub to download.

## How is this different from yt-dlp?

yt-dlp is a general-purpose downloader. Dubbed Video Downloader is a specialized wrapper that:

- Lists available dub languages before downloading
- Selects audio by language code rather than yt-dlp format strings
- Organizes output into `language / channel / title` directories
- Handles quality selection with presets (`best`, `medium`, `low`) instead of requiring format selectors
- Provides crash-safe staged downloads with atomic finalization

## What platforms are supported?

Currently **Linux only**. The project is developed and tested on Linux. Windows and macOS are not supported yet.

## How do I install?

Install from PyPI with pipx (recommended) or pip:

```bash
pipx install dubbed-video-downloader
# pip install dubbed-video-downloader   # alternative
```

FFmpeg and Node.js must be on your system `PATH`. See [Installation](../getting-started/installation.md) for prerequisites and [Quickstart](../getting-started/quickstart.md) for first-run setup.

## What Python version do I need?

Python 3.10 or later. The project is tested on Python 3.10, 3.11, and 3.12 in CI.
