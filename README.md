# YouTube Dubbed Video Downloader

Download YouTube videos or audio with the **dub language you actually want** - Japanese, French, Portuguese, and more.

AI has made it easier than ever for creators to publish the same video with dubbed audio in multiple languages. Channels that once shipped in one language now often offer German, Hindi, Korean, and more on a single upload.

On YouTube, switching to another dub is a few clicks away. Off YouTube, getting the track you want is a different story. Most downloaders grab the default stream, hide alternate languages behind format strings, or save files with names that tell you nothing.

So how do you download a video with the French dub, or save just the Japanese audio? This CLI is built for that: find the dubbed track, pick the quality, and save the result in a predictable place.

> Türkçe dokümantasyon için [README-TR.md](README-TR.md) dosyasına bakın.

## Why this exists

This tool wraps [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [FFmpeg](https://ffmpeg.org/) with a small, purpose-built workflow:

- **Language-first** - list available dubs before you commit to a download.
- **Organized output** - files land under `language / channel / title`, not a random filename in your Downloads folder.
- **Video or audio** - merge dubbed audio into `.mkv`, or save the audio stream on its own.
- **Sensible defaults** - a short setup step stores your preferences; override anything per run when you need to.

Behind the scenes, downloads are staged in a temporary folder and only moved into place when complete. Interrupted runs clean up after themselves. You can preview a download with `--dry-run` before anything hits disk.

## Quick start

**Requirements:** [uv](https://docs.astral.sh/uv/), Python 3.10+, [Node.js](https://nodejs.org/) (for YouTube's JS solver), and **FFmpeg** on your `PATH`.

**Platform:** This project is currently developed and tested on Linux. Windows and macOS are not supported yet and will likely not work as expected.

```bash
git clone https://github.com/Bedirhandd/dubbed-video-downloader.git
cd dubbed-video-downloader
uv sync
uv run dbdvdl init
uv run dbdvdl doctor
```

`doctor` checks Python, your config, FFmpeg, Node.js, and the pinned yt-dlp packages - a quick way to confirm everything is ready.

**First download:**

```bash
# See which dub languages a video offers
uv run dbdvdl langs "https://www.youtube.com/watch?v=VIDEO_ID"

# Download with your default language (set during init)
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID"

# Or pick a language and quality explicitly
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang ko --video-quality 1080p
```

Run `uv run dbdvdl --help` for the full command list.

## Commands


| Command         | What it does                                                              |
| --------------- | ------------------------------------------------------------------------- |
| `init`          | Create `~/.config/dubbed-video-downloader/config.yaml` with your defaults |
| `doctor`        | Verify Python, config, FFmpeg, Node.js, and dependencies                  |
| `langs URL`     | List dubbed audio languages available for a video                         |
| `qualities URL` | Show video and audio quality options for a language                       |
| `download URL…` | Download one or more videos                                               |
| `config show`   | Print your current configuration                                          |
| `config remove` | Remove the config file                                                    |


Useful flags on `download`: `--lang`, `--mode video|audio`, `--video-quality`, `--audio-quality`, `--dry-run`, `--if-exists skip|fail|overwrite`, `--verbose`, `--debug`.

## Where files go

Video downloads are saved as `.mkv`:

```text
~/Downloads/dbdvdl-output/es/<channel>/<title>/<title>.mkv
```

Audio-only downloads use the same folder layout and keep the native extension (`.webm`, `.m4a`, etc.).

During a download, partial files stay in `<output-dir>/tmp/.incomplete/` until the job finishes successfully.

## Configuration

`dbdvdl init` writes a YAML config to `~/.config/dubbed-video-downloader/config.yaml`. You can set defaults for output folder, dub language, download mode, quality presets, network retries, and how to handle files that already exist.

```bash
uv run dbdvdl init --default-lang de
uv run dbdvdl config show
```

CLI flags override config values for a single run. For the full list of keys and behavior, run `uv run dbdvdl init --help` or inspect an initialized config with `config show`.

## Coming soon

- **Batch downloading** - queue playlists, channels, or URL lists with shared defaults
- **Output format customization** - choose container and naming beyond the current defaults
- **GUI** - a desktop interface for the same workflow, without memorizing flags
- **Windows compatibility** - smoother first-run setup and packaging on Windows

## Report an issue

Found a bug, crash, or behavior that does not match the docs? [Open an issue](https://github.com/Bedirhandd/dubbed-video-downloader/issues) on GitHub.

Helpful details to include:

- The command you ran
- What you expected vs. what actually happened
- Your OS and Python version (`dbdvdl doctor` output is useful here)
- Verbose or debug output if the failure is hard to reproduce (`--verbose` or `--debug`)

Suggestions and feature ideas are welcome too - whether or not they appear on the [coming soon](#coming-soon) list.

## Contributing

Pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for branch naming, commit style, and how to run the test suite locally.

## Legal disclaimer

This tool is provided for **educational and personal use only**. Respect [YouTube's Terms of Service](https://www.youtube.com/static?template=terms) and the rights of content creators. Downloading and redistributing videos without permission may violate copyright laws.

## License

This project is licensed under the [MIT License](LICENSE).