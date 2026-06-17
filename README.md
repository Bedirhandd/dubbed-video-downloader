# YouTube Dubbed Video Downloader

[![PyPI version](https://img.shields.io/pypi/v/dubbed-video-downloader)](https://pypi.org/project/dubbed-video-downloader/)
[![License: MIT](https://img.shields.io/github/license/Bedirhandd/dubbed-video-downloader)](LICENSE)
[![Python 3.10](https://img.shields.io/badge/python-3.10-blue)](https://www.python.org/)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-linux-lightgrey)](#quick-start)

Download YouTube videos or audio with the **dub language you actually want** - Japanese, French, Portuguese, and more.

AI has made it easier than ever for creators to publish the same video with dubbed audio in multiple languages. Channels that once shipped in one language now often offer German, Hindi, Korean, and more on a single upload.

On YouTube, switching to another dub is a few clicks away. Off YouTube, getting the track you want is a different story. Most downloaders grab the default stream, hide alternate languages behind format strings, or save files with names that tell you nothing.

So how do you download a video with the French dub, or save just the Japanese audio? This CLI is built for that: find the dubbed track, pick the quality, and save the result in a predictable place.

> Türkçe özet için [README-TR.md](README-TR.md) dosyasına bakın.

## Why this exists

This tool wraps [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [FFmpeg](https://ffmpeg.org/) with a small, purpose-built workflow:

- **Language-first** - list available dubs before you commit to a download.
- **Organized output** - files land under `language / channel / title`, not a random filename in your Downloads folder.
- **Video or audio** - merge dubbed audio into `.mkv`, or save the audio stream on its own.
- **Sensible defaults** - a short setup step stores your preferences; override anything per run when you need to.
- **Crash-safe staging** - downloads go to a temporary staging area first; interrupted runs are cleaned automatically, and finalization is atomic so half-written files never land in your library.

## Quick start

**Platform:** Linux only for now. Windows and macOS are not supported yet.

```bash
pipx install dubbed-video-downloader   # recommended
# pip install dubbed-video-downloader  # alternative
dbdvdl init
dbdvdl doctor
dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID"
```

Install from source with [uv](docs/getting-started/installation.md#install-from-source) if you are contributing to the project.

Prerequisites, a first-download walkthrough, and troubleshooting tips are in [Getting Started](docs/getting-started/quickstart.md).

## Documentation

Full documentation is in the [docs/](docs/index.md) folder:

| Section | What you'll find |
| --- | --- |
| [Getting Started](docs/getting-started/installation.md) | [Installation](docs/getting-started/installation.md), [dependencies](docs/getting-started/dependencies.md), [quickstart](docs/getting-started/quickstart.md) |
| [Commands](docs/commands/overview.md) | [init](docs/commands/init.md), [doctor](docs/commands/doctor.md), [langs](docs/commands/langs.md), [qualities](docs/commands/qualities.md), [download](docs/commands/download.md), [config](docs/commands/config.md) |
| [Configuration](docs/configuration/overview.md) | [Config keys](docs/configuration/config-keys.md), [management](docs/configuration/management.md) |
| [Usage examples](docs/usage-examples/index.md) | Practical recipes for downloads, languages, quality, scripting, and [troubleshooting](docs/usage-examples/troubleshooting.md) |
| [Features](docs/features/language-resolution.md) | [Language resolution](docs/features/language-resolution.md), [quality](docs/features/quality-selection.md), [download modes](docs/features/download-modes.md), [output layout](docs/features/output-layout.md), [staged downloads](docs/features/staged-downloads.md) |
| [FAQ](docs/faq/general.md) | [Setup](docs/faq/installation-and-setup.md), [languages](docs/faq/language-and-dubs.md), [downloads](docs/faq/quality-and-downloads.md), [troubleshooting](docs/faq/troubleshooting.md) |
| [Architecture](docs/architecture/overview.md) | For contributors: [modules](docs/architecture/modules.md), [download pipeline](docs/architecture/download-pipeline.md), [testing](docs/architecture/testing.md) |

## Coming soon

- **Batch downloading** - queue playlists, channels, or URL lists with shared defaults
- **Output format customization** - choose container and naming beyond the current defaults
- **GUI** - a desktop interface for the same workflow, without memorizing flags
- **Windows compatibility** - smoother first-run setup and packaging on Windows

## Report an issue

Found a bug or unexpected behavior? [Open an issue](https://github.com/Bedirhandd/dubbed-video-downloader/issues) on GitHub. The [troubleshooting guide](docs/usage-examples/troubleshooting.md) and [FAQ](docs/faq/troubleshooting.md) may help first.

## Contributing

Pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) and the [development FAQ](docs/faq/usage-and-development.md).

## Legal disclaimer

This tool is provided for **educational and personal use only**. Respect [YouTube's Terms of Service](https://www.youtube.com/static?template=terms) and the rights of content creators. Downloading and redistributing videos without permission may violate copyright laws.

## License

This project is licensed under the [MIT License](LICENSE).
