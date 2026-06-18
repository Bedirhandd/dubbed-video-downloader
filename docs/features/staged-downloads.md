# Staged Downloads (Crash-Safe)

Downloads go through a staging system before reaching the final output location:

1. **Staging directory:** Files are downloaded into `output_dir/tmp/.incomplete/<run-id>/` where `<run-id>` is a unique identifier (`<timestamp>-<pid>-<uuid>`).

2. **Atomic finalization:** When the download completes successfully, the file is moved from staging to the final output path:
   - **Same filesystem:** A hard link is created (instant, no extra disk usage)
   - **Different filesystem:** The file is copied through a `.dubbed-video-downloader-finalizing/` directory with atomic no-clobber rename using platform-specific syscalls

3. **Crash recovery:** If the process crashes or is killed mid-download:
   - The staging directory remains in `tmp/.incomplete/`
   - On the next download, stale staging directories are detected (by attempting to acquire a non-blocking lock) and cleaned up
   - Any partial finalization artifacts (files in `.dubbed-video-downloader-finalizing/`) are also cleaned

4. **Signal safety:** `SIGTERM` and `SIGHUP` are trapped during download. The signal handler raises `SystemExit`, which triggers the context manager cleanup, removing the staging directory.

## File Exists Behavior

Three strategies for handling existing output files:

| Behavior | CLI Flag | Effect |
| --- | --- | --- |
| Skip | `--if-exists skip` | Silently skip the download. The URL is not re-processed. Status is shown as `Skipped`. |
| Fail | `--if-exists fail` | Raise a `DownloadError` immediately. The download is not attempted. |
| Overwrite | `--if-exists overwrite` | Download the file again and replace the existing one. |

The default behavior is set in config (`default_exists_behavior`), overridable per-command with `--if-exists`.
