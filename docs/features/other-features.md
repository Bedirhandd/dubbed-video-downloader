# Other Features

## Dry Run

The `--dry-run` flag on the `download` command performs a full validation pass without downloading:

- Fetches video metadata
- Resolves the requested language
- Plans the output path
- Estimates disk usage (from format filesize metadata)
- Checks whether the output file already exists
- Reports what `--if-exists` would do (skip/fail/overwrite)

Example output:

```
Dry run: no files will be downloaded or created.
Title: Pasta Recipe
Channel: CookingChannel
Language: fr
Mode: video
Video quality: 1080p
Audio quality: best
Available languages: en, es, fr, ja, ko
Output: ~/Downloads/dbdvdl-output/fr/CookingChannel/Pasta Recipe/Pasta Recipe.mkv
Estimated disk usage: ~250 MB
If output exists: skip
Output exists: no
Dry run OK
```

## Disk Usage Estimation and Confirmation

Before each download, the system estimates the required disk space from the format metadata. When `ask_for_disk_usage` is enabled in config, you are prompted:

```
This download is estimated to use ~250 MB of disk space. Continue? [y/N]:
```

- Answer `y` to proceed, `n` to cancel (skips this URL and continues to the next, or exits)
- Use `--yes` / `-y` to auto-approve all disk usage prompts for the run
- In non-interactive environments, disk usage confirmation is refused unless `--yes` is provided (to prevent hanging scripts)

## Network Retry

Transient network failures during metadata extraction and media download are automatically retried:

- **Retry count:** Configurable via `retry_on_network_failure` (default: 3, set 0 to disable)
- **Scope:** Applied to yt-dlp's `retries`, `fragment_retries`, and `extractor_retries`
- **Backoff:** Exponential backoff with a maximum of 8 seconds per attempt, plus a random jitter of up to 1 second

## Environment Check (Doctor)

The `doctor` command runs a comprehensive environment check available as `dbdvdl doctor`. Each check is independent -- a failure in one does not prevent others from running. The command exits with code 1 if any check fails.

## Multiple URL Downloads

The `download` command accepts multiple URLs:

```bash
uv run dbdvdl download "URL1" "URL2" "URL3" --lang ja
```

Each URL is processed independently. If one URL fails, processing continues with the next. The exit code is 1 if any URL failed.

## Progress Display

In interactive terminals (and when not using `--verbose`, `--debug`, or `--dry-run`), a status spinner shows the current download stage:

```
[done] Checking configuration...
[done] Fetching metadata...
[done] Checking available languages...
[done] Selecting qualities...
Downloading media...  2.5 MB/s - ETA: 00:01:23 - 45% Completed
```

During the download phase, progress is updated approximately every 250ms with:
- **Speed:** Current download speed (e.g., `2.5 MB/s`)
- **ETA:** Estimated time remaining (HH:MM:SS)
- **Percentage:** Completion percentage

When a stage completes successfully, it is prefixed with `[done]`. If the process fails during a stage, it is prefixed with `[failed]`.

### Verbose and Debug Modes

- `--verbose` / `-v`: Shows yt-dlp's own progress bar, info messages, and warnings. The custom status display is replaced by yt-dlp's output.
- `--debug`: Shows yt-dlp's debug output and, on error, the full Python traceback to stderr.
