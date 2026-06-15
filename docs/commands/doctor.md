# `dbdvdl doctor`

**Description:** Run environment and configuration checks. Verifies that Python, the config file, the output directory, FFmpeg, Node.js, and required Python packages are all present and functional.

**Usage:**

```
uv run dbdvdl doctor
```

## Options

None.

## Output

Displays a table of checks with their status (`OK` or `FAIL`) and detail. Exits with code `1` if any check fails.

Example output:

```
System check

Python         OK     3.12.3
Config         OK     /home/user/.config/dubbed-video-downloader/config.yaml
Output directory OK    ~/Downloads/dbdvdl-output exists and is writable
FFmpeg         OK     7.1.1 (/usr/bin/ffmpeg)
Node           OK     v22.11.0 (/usr/bin/node)
yt-dlp         OK     2026.3.17
yt-dlp-ejs     OK     0.8.0
```
