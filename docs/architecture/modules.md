# Module Responsibilities

## `cli.py` -- CLI Layer

The Typer application entry point. Defines all commands, subcommands, arguments, and options. Responsibilities:

- **Command definitions:** `init`, `doctor`, `langs`, `qualities`, `download`, `config show`, `config remove`
- **Input validation and normalization:** Delegates to `config`, `languages`, and `quality` modules, converts errors to colored stderr output and non-zero exit codes
- **Configuration resolution:** Loads config, then applies CLI overrides to produce effective values
- **Output formatting:** Rich/Typer-based output, progress spinners, stage markers, dry-run plan display, quality reports, download result confirmation
- **Non-interactive guard:** Refuses to prompt for disk usage confirmation when stdin is not a TTY unless `--yes` is provided

Key internal types:
- `_DownloadInvocation` -- frozen dataclass holding all resolved download parameters
- `_DownloadStatusRenderer` -- context manager managing the Rich status spinner with stage updates and progress rendering, throttled to 250ms intervals

## `core.py` -- Download Orchestration

The core engine. Orchestrates the full download lifecycle and contains all yt-dlp integration. Responsibilities:

- **Metadata extraction:** `get_video_info()` calls yt-dlp's `extract_info()` with `download=False`
- **Language resolution:** Delegates to `languages` module to match requested language against video audio tracks
- **Quality selection:** Delegates to `quality` module to build yt-dlp format selectors
- **Output path planning:** Uses yt-dlp's `prepare_filename()` to determine the final output path from the format template
- **Download execution:** Creates yt-dlp `YoutubeDL` instances with resolved options, connects progress hooks for status display
- **Staging system:** Downloads go into `output_dir/tmp/.incomplete/<run-id>/` with a lock-based concurrency model
- **Atomic finalization:** Moves files from staging to final output using hard links (same filesystem) or copy+atomic rename (cross-filesystem), with platform-specific no-clobber semantics
- **Stale cleanup:** On each download start, cleans up orphaned incomplete directories from previous crashed/interrupted runs
- **Signal handling:** Traps `SIGTERM` and `SIGHUP` during download to trigger cleanup via context manager

Key data types:
- `DownloadStage` enum -- 11 stages tracking the download pipeline
- `DownloadPlan` dataclass -- description of what will be downloaded
- `DownloadResult` dataclass -- outcome of a completed download
- `DownloadProgress` dataclass -- speed, ETA, percentage from yt-dlp progress hooks
- `QualityReport` dataclass -- available quality options for a URL+language

## `config.py` -- Configuration Management

Handles config file I/O, validation, and normalization. Responsibilities:

- **Config path:** `Path.home() / ".config" / "dubbed-video-downloader" / "config.yaml"`
- **File operations:** `load_config()`, `write_config()`, `remove_config_dir()`
- **POSIX permissions:** `write_config()` creates the config directory as `0700` and `config.yaml` as `0600`; `config_permissions_warning()` supports doctor warnings for existing loose permissions
- **Parsing:** YAML via `PyYAML`, with `config.yaml` serialization in stable key order
- **Validation:** Required keys check, type validation, path expansion (`~` and env vars), language code validation
- **Normalization:** `normalize_output_dir()`, `normalize_ffmpeg_path()`, `normalize_default_lang()`, `normalize_download_mode()`, `normalize_video_quality()`, `normalize_audio_quality()`, `normalize_retry_on_network_failure()`, `normalize_exists_behavior()`, `normalize_ask_for_disk_usage()`

Key data type: `AppConfig` frozen dataclass with all config fields.

## `languages.py` -- Language Code Handling

BCP-47 language code validation, normalization, and resolution against video metadata. Responsibilities:

- **User code validation:** `normalize_language_code()` -- standardizes user input via `langcodes`, rejects invalid/undefined codes
- **Metadata tag validation:** `normalize_video_language_tag()` -- validates language tags from YouTube format metadata, returns None for invalid/undefined tags so they can be skipped with a warning
- **Collection:** `collect_available_audio_langs()` -- scans yt-dlp format info for audio-only tracks (vcodec=none, acodec present) and extracts their language metadata
- **Resolution:** `resolve_language_for_video()` -- matches the user's canonical BCP-47 code against the raw metadata tags. Used `langcodes.closest_supported_match()` for fuzzy matching (max distance 10) when the request does not include territory/script. Falls back to exact match when territory/script is specified.

Key data type: `AudioLanguageInventory` -- frozenset of valid language tags plus skipped-invalid counts and tags.

## `quality.py` -- Quality Selection

Video and audio quality definitions and yt-dlp format selector construction. Responsibilities:

- **Quality enums:** `VideoQuality` (presets: best/medium/low, exact with height 144-8640), `AudioQuality` (presets: best/medium/low)
- **Normalization:** `normalize_video_quality()`, `normalize_audio_quality()` -- parse user input into typed quality objects
- **Format selector construction:** Builds yt-dlp format selection strings
  - Video: `bv` (best), `bv[height=N]` (exact/medium/low)
  - Audio: targeted by `format_id` or bitrate field when every candidate reports bitrate metadata for `best`, `medium`, and `low`; falls back to `bestaudio[language="LANG"]` or `worstaudio[language="LANG"]` when bitrate metadata is missing from any candidate (`best`) or from all candidates (`medium`/`low`); when multiple raw language casings match, fallbacks use one regex union language filter instead of a `/` precedence chain
- **Quality reporting:** `get_available_video_heights()`, `get_audio_quality_candidates()`, `format_video_quality_labels()`, `format_audio_quality_labels()`
- **Selection:** `resolve_quality_selection()` -- combines video and audio selectors with `+` for video mode, returns `QualitySelection` with selected labels and informational notes

Key data types: `VideoQuality`, `AudioQuality`, `AudioQualityCandidate`, `QualitySelection`.

## `doctor.py` -- Environment Checks

Runs a series of system checks for the `doctor` command. Checks:
- Python version >= 3.10
- Config file exists and is valid
- Config file permissions are owner-only on POSIX (warning only; does not fail the command)
- Output directory exists or can be created, is writable
- FFmpeg is found and executable
- Node.js is found and executable
- yt-dlp and yt-dlp-ejs packages are installed

Returns `CheckResult` dataclasses with name, ok status, and detail message.

## `errors.py` -- Error Hierarchy

A focused exception hierarchy rooted at `DubbedVideoDownloaderError(RuntimeError)`:

```
DubbedVideoDownloaderError
├── ConfigError              # Config missing/invalid
├── QualityError             # Quality input/metadata can't produce safe selector
├── MetadataExtractionError  # Video metadata can't be extracted
├── InvalidLanguageCodeError # User-supplied language code is invalid
├── LanguageNotFoundError    # Requested dub language unavailable
└── DownloadError            # Media download or planning fails
```

## `download_mode.py` and `exists_behavior.py` -- Simple Enums

Two small modules defining enums with normalization functions:

- `DownloadMode`: `VIDEO = "video"`, `AUDIO = "audio"`
- `FileExistsBehavior`: `SKIP = "skip"`, `FAIL = "fail"`, `OVERWRITE = "overwrite"`

## `yt_dlp_types.py` -- Type Aliases

Conditional type aliases for yt-dlp's internal types:
- `InfoDict` -- the dictionary returned by `extract_info()`
- `YdlParams` -- the parameter dictionary passed to `YoutubeDL()`

At type-check time, these resolve to yt-dlp's internal `_InfoDict` and `_Params` types. At runtime, they are `dict[str, Any]`.
