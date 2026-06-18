# `dbdvdl doctor`

**Description:** Run environment and configuration checks. Verifies that Python, the config file, config file permissions, the output directory, FFmpeg, Node.js, and required Python packages are all present and functional.

**Usage:**

```
dbdvdl doctor
```

## Options

None.

## Output

Displays a table of checks with their status (`OK` or `FAIL`) and detail. Exits with code `1` if any check fails.

The `Config permissions` check always reports `OK` when the config file loaded successfully. On POSIX systems it warns when the config directory or file is readable by other users, but it does not fail the command or block downloads.

Example output:

```
System check

Python            OK     3.12.3
Config            OK     /home/user/.config/dubbed-video-downloader/config.yaml
Config permissions OK    owner-only permissions
Output directory  OK     ~/Downloads/dbdvdl-output exists and is writable
FFmpeg            OK     7.1.1 (/usr/bin/ffmpeg)
Node              OK     v22.11.0 (/usr/bin/node)
yt-dlp            OK     2026.6.9
yt-dlp-ejs        OK     0.8.0
```

When an existing config was created with loose permissions, `Config permissions` still reports `OK` but the detail includes a recommended `chmod` fix:

```
Config permissions OK    permissions are not owner-only; recommended chmod 600 config.yaml and chmod 700 /home/user/.config/dubbed-video-downloader
```

On non-POSIX platforms, the detail is `not applicable on this platform`.

## Checks

| Check | Fails command? | Description |
| --- | --- | --- |
| Python | Yes | Python version must be 3.10 or newer |
| Config | Yes | Config file must exist and parse correctly |
| Config permissions | No | On POSIX, warns when the config directory or file is not owner-only (`0700` / `0600`) |
| Output directory | Yes | Configured output directory must exist or be creatable and writable |
| FFmpeg | Yes | Configured FFmpeg executable must exist and run |
| Node | Yes | `node` must be found on `PATH` and run |
| yt-dlp | Yes | Python package must be installed |
| yt-dlp-ejs | Yes | Python package must be installed |

When the config check fails, `Config permissions`, `Output directory`, and `FFmpeg` report `FAIL` with `config unavailable` because they depend on a loaded config.

Example output when config is missing:

```
System check

Python            OK     3.12.3
Config            FAIL   Config file not found at /home/user/.config/dubbed-video-downloader/config.yaml. Run `dbdvdl init` to create it.
Config permissions FAIL   config unavailable
Output directory  FAIL   config unavailable
FFmpeg            FAIL   config unavailable
Node              OK     v22.11.0 (/usr/bin/node)
yt-dlp            OK     2026.6.9
yt-dlp-ejs        OK     0.8.0
```
