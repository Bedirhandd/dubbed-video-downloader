# YouTube Dubbed Video Downloader

[License: MIT](https://github.com/Bedirhandd/dubbed-video-downloader/blob/main/LICENSE)
[Python 3.10+](https://www.python.org/)
[Platform](https://github.com/Bedirhandd/dubbed-video-downloader#quick-start)

Download YouTube videos or audio with the **dub language you actually want** — Japanese, French, Portuguese, and more.

This CLI wraps [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [FFmpeg](https://ffmpeg.org/) with a language-first workflow: list available dubs, pick quality, and save files under `language / channel / title`.

- **Language-first** - list available dubs before you commit to a download.
- **Organized output** - files land under `language / channel / title`.
- **Video or audio** - merge dubbed audio into `.mkv`, or save the audio stream on its own.
- **Sensible defaults** - a short setup step stores your preferences.
- **Crash-safe staging** - downloads go to a temporary staging area first; interrupted runs are cleaned automatically, and finalization is atomic so half-written files never land in your library.

## Requirements

**Platform:** Linux only for now. Windows and macOS are not supported yet.

Install these on your system `PATH` before using `dbdvdl`:


| Dependency                     | Purpose                                    |
| ------------------------------ | ------------------------------------------ |
| [FFmpeg](https://ffmpeg.org/)  | Merge video and audio streams              |
| [Node.js](https://nodejs.org/) | YouTube JavaScript solver (via yt-dlp-ejs) |


## Install

```bash
pipx install dubbed-video-downloader   # recommended
# pip install dubbed-video-downloader  # alternative
dbdvdl init
dbdvdl doctor
dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID"
```

## Documentation

Full documentation lives on GitHub:


| Section         | Links                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Getting Started | [Installation](https://github.com/Bedirhandd/dubbed-video-downloader/blob/main/docs/getting-started/installation.md), [dependencies](https://github.com/Bedirhandd/dubbed-video-downloader/blob/main/docs/getting-started/dependencies.md), [quickstart](https://github.com/Bedirhandd/dubbed-video-downloader/blob/main/docs/getting-started/quickstart.md)                                                                                                                                                                                                                                                                                                                                                                 |
| Commands        | [Overview](https://github.com/Bedirhandd/dubbed-video-downloader/blob/main/docs/commands/overview.md) — [init](https://github.com/Bedirhandd/dubbed-video-downloader/blob/main/docs/commands/init.md), [doctor](https://github.com/Bedirhandd/dubbed-video-downloader/blob/main/docs/commands/doctor.md), [langs](https://github.com/Bedirhandd/dubbed-video-downloader/blob/main/docs/commands/langs.md), [qualities](https://github.com/Bedirhandd/dubbed-video-downloader/blob/main/docs/commands/qualities.md), [download](https://github.com/Bedirhandd/dubbed-video-downloader/blob/main/docs/commands/download.md), [config](https://github.com/Bedirhandd/dubbed-video-downloader/blob/main/docs/commands/config.md) |
| Configuration   | [Overview](https://github.com/Bedirhandd/dubbed-video-downloader/blob/main/docs/configuration/overview.md), [config keys](https://github.com/Bedirhandd/dubbed-video-downloader/blob/main/docs/configuration/config-keys.md)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Usage & FAQ     | [Examples](https://github.com/Bedirhandd/dubbed-video-downloader/blob/main/docs/usage-examples/index.md), [troubleshooting](https://github.com/Bedirhandd/dubbed-video-downloader/blob/main/docs/usage-examples/troubleshooting.md), [FAQ](https://github.com/Bedirhandd/dubbed-video-downloader/blob/main/docs/faq/general.md)                                                                                                                                                                                                                                                                                                                                                                                              |


[Index of all docs](https://github.com/Bedirhandd/dubbed-video-downloader/blob/main/docs/index.md)

## Report an issue

[Open an issue](https://github.com/Bedirhandd/dubbed-video-downloader/issues) on GitHub.

## Contributing

See [CONTRIBUTING.md](https://github.com/Bedirhandd/dubbed-video-downloader/blob/main/CONTRIBUTING.md) on GitHub.

## Legal disclaimer

This tool is provided for **educational and personal use only**. Respect [YouTube's Terms of Service](https://www.youtube.com/static?template=terms) and the rights of content creators.

## License

[MIT License](https://github.com/Bedirhandd/dubbed-video-downloader/blob/main/LICENSE)