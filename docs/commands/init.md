# `dbdvdl init`

**Description:** Create the required user configuration file at `~/.config/dubbed-video-downloader/config.yaml`. Runs an interactive prompt for each setting unless values are provided via options or `--default` is used.

**Usage:**

```
uv run dbdvdl init [OPTIONS]
uv run dbdvdl config init [OPTIONS]   # identical behavior
```

Both `dbdvdl init` and `dbdvdl config init` are the same command. Either can be used.

## Options

### `--output-dir`, `-o`

| Property | Value |
| --- | --- |
| Type | `str` |
| Default | Prompted (default: `~/Downloads/dbdvdl-output`) |
| Description | Absolute directory where downloads will be saved. Supports `~` expansion and environment variable expansion. |

### `--ffmpeg-path`

| Property | Value |
| --- | --- |
| Type | `str` |
| Default | Prompted (default: `ffmpeg`) |
| Description | Path to the FFmpeg executable, or `ffmpeg` to use the system PATH. |

### `--default-lang`

| Property | Value |
| --- | --- |
| Type | `str` |
| Default | Prompted (default: `en`) |
| Description | Default dub language code to use when `--lang` is omitted on the download command. Must be a valid BCP-47 language code (e.g., `en`, `eng`, `en-US`, `tr`). |

### `--default-download-mode`

| Property | Value |
| --- | --- |
| Type | `video` \| `audio` |
| Default | Prompted (default: `video`) |
| Description | Default download mode to use when `--mode` is omitted on the download command. |

### `--default-video-quality`

| Property | Value |
| --- | --- |
| Type | `str` |
| Default | Prompted (default: `best`) |
| Description | Default video quality for video downloads. Valid values: `best`, `medium`, `low`, or an exact resolution from `144p` through `8640p`. |

### `--default-audio-quality`

| Property | Value |
| --- | --- |
| Type | `str` |
| Default | Prompted (default: `best`) |
| Description | Default dubbed audio quality. Valid values: `best`, `medium`, or `low`. |

### `--retry-on-network-failure`

| Property | Value |
| --- | --- |
| Type | `int` |
| Default | Prompted (default: `3`) |
| Description | How many times to retry transient metadata, extraction, and media download failures. Must be a non-negative integer. `0` disables retries. |

### `--default-exists-behavior`

| Property | Value |
| --- | --- |
| Type | `skip` \| `fail` \| `overwrite` |
| Default | Prompted (default: `skip`) |
| Description | Default behavior when the planned output file already exists. `skip` silently skips the download, `fail` raises an error, `overwrite` replaces the existing file. |

### `--ask-for-disk-usage` / `--no-ask-for-disk-usage`

| Property | Value |
| --- | --- |
| Type | `bool` |
| Default | Prompted (default: `false` / `--no-ask-for-disk-usage`) |
| Description | When enabled, downloads prompt for confirmation after showing an estimated disk usage. When disabled, downloads proceed without confirmation. |

### `--force`

| Property | Value |
| --- | --- |
| Type | `bool` |
| Default | `False` |
| Description | Overwrite the existing config file without prompting. |

### `--default`

| Property | Value |
| --- | --- |
| Type | `bool` |
| Default | `False` |
| Description | Write config using built-in defaults without interactive prompts. Useful for scripting or CI environments. |

## Examples

```bash
# Interactive setup (prompts for each value)
uv run dbdvdl init

# Use all defaults without prompts
uv run dbdvdl init --default

# Set specific values non-interactively
uv run dbdvdl init --output-dir ~/Videos --default-lang tr --default-download-mode audio

# Overwrite an existing config
uv run dbdvdl init --force --default-lang de
```

## File Permissions

On POSIX systems, a successful `init` creates `~/.config/dubbed-video-downloader/` with mode `0700` and `config.yaml` with mode `0600`. Overwriting with `--force` applies the same permissions again.

Valid configs with looser permissions continue to load. Use `dbdvdl doctor` to check whether the config directory and file are owner-only.
