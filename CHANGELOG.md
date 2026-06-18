# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0](https://github.com/Bedirhandd/dubbed-video-downloader/compare/v0.1.0...v0.2.0) - 2026-06-18

### Added

- `**dbdvdl` CLI** — a full command-line tool replaces the old single-file script. Commands include `init`, `doctor`, `langs`, `qualities`, `download`, and `config`.
- **Persistent configuration** — settings are stored in `~/.config/dubbed-video-downloader/config.yaml` instead of editing source code. Run `dbdvdl init` to set up output directory, FFmpeg path, default language, quality presets, retry count, and more.
- **Non-interactive setup** — `dbdvdl init --default` creates a config with sensible defaults without prompts; individual values can also be passed as flags.
- **Environment checks** — `dbdvdl doctor` verifies Python, config, output directory, FFmpeg, Node.js, yt-dlp, and yt-dlp-ejs before you download anything.
- **Inspect before you download** — `dbdvdl langs` lists available dubbed languages for a video; `dbdvdl qualities` shows video and audio quality options for a chosen language.
- **Two download modes** — save a dubbed video as `.mkv` (`--mode video`) or extract only the dubbed audio track (`--mode audio`).
- **Quality selection** — choose video resolution (`best`, `medium`, `low`, or a specific value like `720p`) and audio quality (`best`, `medium`, `low`) per download or as defaults in config.
- **Dry-run preview** — `--dry-run` shows title, channel, language, planned output path, estimated disk usage, and what would happen if the file already exists — without downloading anything.
- **Live progress** — during downloads, the CLI shows speed, ETA, and completion percentage in real time.
- **Post-download feedback** — after a successful download, the actual file size and the verified output path are displayed.
- **Disk usage confirmation** — when enabled in config, you are asked to confirm before a download starts if it will use a significant amount of space.
- **Existing file handling** — `--if-exists` lets you skip, fail, or overwrite when the output file is already there (also configurable as a default).
- **Network retry** — transient network failures are retried automatically; the retry count is configurable.
- **Language normalization** — language codes follow BCP-47 conventions, so inputs like `pt-BR` or `zh-Hans` are handled consistently.
- **Verbose and debug output** — `--verbose` shows yt-dlp's own output; `--debug` adds even more detail for troubleshooting.
- **Config management** — `dbdvdl config show` prints your current settings; `dbdvdl config remove` deletes the config directory.
- **Documentation** — comprehensive guides under `docs/` covering installation, commands, configuration, features, usage examples, FAQ, and architecture.
- **PyPI distribution** — install with `pipx install dubbed-video-downloader` or `pip install dubbed-video-downloader`; no need to clone the repository for normal use.
- **Continuous integration** — GitHub Actions runs tests, linting (Ruff), type checking (mypy), coverage reporting, and dependency vulnerability audits on every push.

### Changed

- **From script to package** — the project is now a structured Python package with a `dbdvdl` entry point instead of a `script.py` you edit by hand.
- **Output directory** — must be an absolute path, set once in config and reused for every download.
- **README** — slimmed down with links to the full documentation site for detailed guidance.
- **Test framework** — the test suite was migrated from unittest to pytest for clearer structure and better fixtures.

### Removed

- `**script.py` workflow** — configuration constants (`DUB_LANGUAGE`, `FFMPEG_PATH`, `VIDEO_URLS`) inside a Python file are no longer the way to use this tool. Use `dbdvdl init` and CLI flags instead.

### Fixed

- **Dubbed video format selection** — video streams without their own audio are correctly paired with the chosen dubbed audio track, so you get the dub you asked for instead of the default track.
- **Audio language matching** — language selection now works the same way for audio as it does for resolution: exact matches for regional and script variants, sensible fallbacks when a precise tag is not available, and support for streams that report language in metadata rather than only in the format name.
- **Audio quality "best"** — when multiple audio streams qualify, the highest-bitrate candidate is chosen; if some streams lack bitrate metadata, the selector falls back gracefully instead of failing.
- **Crash-safe downloads** — downloads are staged in a temporary area first and moved to the final location only when complete. Interrupted runs are cleaned up automatically; partial files never land in your library.
- **Cross-filesystem output** — finalizing a download to a different filesystem (for example, an external drive) works reliably via copy or hard link, with cleanup if something goes wrong mid-transfer.
- **Race conditions** — concurrent writes to the same output path and redirected staging directories are detected and rejected.
- **Approval re-check** — if you confirm a disk-usage prompt, the tool re-checks whether the output file appeared in the meantime before proceeding.
- **FFmpeg validation** — missing or broken FFmpeg is reported before the download starts, not halfway through.
- **URL validation** — only `http://` and `https://` URLs are accepted; other schemes are rejected at the CLI level.
- **Metadata validation** — unexpected shapes in yt-dlp's response are caught early with a clear error instead of causing obscure failures later.
- **Init guard** — `dbdvdl init` fails immediately if a config file already exists, preventing accidental overwrites.
- **Clearer language errors** — invalid `--lang` values show an "Input error" message that is easier to spot among other output.
- **Retry timing** — the sleep interval between network retries now matches yt-dlp's expected callback contract.
- **Error messages** — unsafe staging path errors and inspection command failures surface readable messages instead of raw tracebacks.

### Security

- **Config file permissions** — on Linux and other POSIX systems, the config directory is created as `0700` and the config file as `0600`, so only your user account can read your settings.
- **Dependency audits** — CI checks for known vulnerabilities in project dependencies; yt-dlp was updated to address reported advisories.

## [0.1.0](https://github.com/Bedirhandd/dubbed-video-downloader/releases/tag/v0.1.0) - 2026-05-10

### Added

- **Initial release** — a single Python script (`script.py`) that downloads YouTube videos with a chosen dubbed audio track.
- **Dub language selection** — set the target language (for example `tr`, `en`, `ja`) via a `DUB_LANGUAGE` constant in the script; the tool checks that the requested dub exists before downloading.
- **MKV output** — merges the best video stream with the selected dubbed audio into a `.mkv` file using FFmpeg.
- **Organized folder layout** — saves files under `Videos/<language>/<channel>/<title>/<title>.mkv`.
- **Batch URLs** — add multiple YouTube links to a `VIDEO_URLS` list in the script and download them in one run.
- **Optional FFmpeg path** — override the FFmpeg location with `FFMPEG_PATH` when it is not on your system `PATH`.
- **uv project setup** — dependencies managed with [uv](https://docs.astral.sh/uv/); `uv sync` installs yt-dlp and yt-dlp-ejs.
- **MIT License**.
- **Contributing guidelines** (`CONTRIBUTING.md`) and README in English and Turkish (`README-TR.md`).

