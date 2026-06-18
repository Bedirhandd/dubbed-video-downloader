# Download Pipeline

## Data Flow

Here is the complete flow for a `download` command:

```
User runs: dbdvdl download URL --lang ja --video-quality 1080p

1. CLI layer (cli.py)
   ├── Load config from ~/.config/dubbed-video-downloader/config.yaml
   ├── Apply CLI overrides (--lang, --video-quality, etc.)
   ├── Validate and normalize all values
   └── For each URL:
       ├── Report stage: CHECKING_CONFIG
       ├── Report stage: PREPARING_OPTIONS

2. core.download() (core.py)
   ├── Report stage: FETCHING_METADATA
   │   └── yt-dlp extract_info(url, download=False)
   │       └── Returns InfoDict with formats, title, uploader, etc.
   │
   ├── Report stage: CHECKING_LANGUAGES
   │   └── languages.resolve_language_for_video("ja", inventory)
   │       └── Matches against audio format language tags
   │       └── Returns raw metadata tag (e.g., "ja")
   │
   ├── Report stage: SELECTING_QUALITIES
   │   └── quality.resolve_quality_selection(info, lang, mode, vq, aq)
   │       └── Builds format selector: "bv[height=1080]+bestaudio[language=\"ja\"]"
   │
   ├── Report stage: PLANNING_OUTPUT
   │   └── yt-dlp prepare_filename() with format template
   │       └── Template: output_dir/ja/uploader/title/title.ext
   │
   ├── Check exists_behavior (skip/fail/overwrite)
   │   ├── SKIP: return DownloadResult(status=SKIPPED)
   │   └── FAIL: raise DownloadError if output exists
   │
   ├── Optional: approval_callback (disk usage confirmation)
   │   ├── If cancelled: return DownloadResult(status=CANCELLED)
   │   └── Re-check exists_behavior after approval closes the confirmation race window
   │
   ├── Report stage: PREPARING_OUTPUT_DIR
   │   ├── Cleanup stale incomplete downloads
   │   └── Create staging run directory:
   │       output_dir/tmp/.incomplete/<timestamp>-<pid>-<uuid>/
   │
   ├── Report stage: DOWNLOADING_MEDIA
   │   └── yt-dlp YoutubeDL.download([url])
   │       ├── Downloads to staging directory
   │       ├── Progress hooks update CLI spinner (throttled to 250ms)
   │       └── Postprocessor hook updates MERGING_MEDIA stage
   │
   ├── Report stage: FINALIZING_OUTPUT
   │   └── _finalize_staged_download()
   │       ├── If same filesystem: hard link staging -> final
   │       ├── If cross-filesystem: copy to .dubbed-video-downloader-finalizing/, then atomic rename
   │       └── Cleanup staging directory
   │
   └── Return DownloadResult(status=DOWNLOADED, output_path=...)

3. CLI layer (cli.py)
   ├── Print success: "Finished", "Saved to <path>", "Size: <size>"
   └── On error: print colored error message, optionally show traceback with --debug
```

## Staging and Finalization Architecture

The staging system ensures downloads are atomic and crash-safe.

### Directory Layout

```
output_dir/
├── tmp/
│   └── .incomplete/                    # All staging lives here
│       ├── .cleanup.lock               # Lock file for stale cleanup
│       └── <run-id>/                   # Per-download staging directory
│           ├── .lock                    # Run lock (prevents concurrent cleanup)
│           ├── run.json                 # Staging metadata (application, pid, timestamp)
│           └── <lang>/<channel>/<title>/<title>.ext  # Downloaded file
└── <lang>/<channel>/<title>/           # Final output location
    ├── <title>.ext                     # Downloaded file
    └── .dubbed-video-downloader-finalizing/  # Cross-filesystem copy staging
        └── <run-id>.tmp                # Temp copy during finalization
```

### Lock Model

Two levels of locking using `_StagingLock`:

1. **Cleanup lock** (`INCOMPLETE_CLEANUP_LOCK_FILENAME`): Prevents concurrent stale cleanup
2. **Run lock** (`RUN_LOCK_FILENAME`): Marks a staging directory as active. Held during the entire download. Released before cleanup removes the directory.

On POSIX systems, locks use `fcntl.flock()`. On Windows, `msvcrt.locking()`.

### Stale Cleanup

At the start of each download, `_cleanup_stale_incomplete_downloads()` runs:
- Acquires the non-blocking cleanup lock
- Iterates staging directories, reads `run.json` metadata
- For each directory, attempts to acquire the run lock non-blocking
- If the lock is acquired (meaning the original process is gone), cleans up any finalizing copy artifacts and removes the staging directory

### Finalization

The finalization process depends on whether the staging and final output directories are on the same filesystem:

**Same filesystem (fast path):**
1. `os.link()` -- create a hard link from staging file to final output
2. Delete staging file (now just an additional hard link to the same inode)

**Cross-filesystem (fallback):**
1. Copy to `output_dir/<lang>/.../ ... .dubbed-video-downloader-finalizing/<run-id>.tmp`
2. Atomic no-clobber rename to final path using platform-specific syscalls:
   - Linux: `renameat2` with `RENAME_NOREPLACE` flag
   - macOS: `renamex_np` with `RENAME_EXCL` flag
   - Windows: `MoveFileExW` with `MOVEFILE_WRITE_THROUGH` flag
3. Delete staging file

All finalization operations are crash-safe: if the process dies mid-finalization, the `run.json` metadata records the finalizing copy directories, and the next stale cleanup run removes them.

### Signal Handling

During download, `SIGTERM` and `SIGHUP` are trapped and converted to `SystemExit`. The `_DownloadStagingRun` context manager's `__exit__` is then invoked, which releases the run lock and removes the staging directory, preventing stale data from accumulating.
