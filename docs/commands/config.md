# `dbdvdl config`

Configuration management subcommands.

## `dbdvdl config show`

**Description:** Show the resolved user configuration.

**Usage:**

```
dbdvdl config show
```

### Options

None.

### Output

Prints every config key with its current value:

```
Config path: /home/user/.config/dubbed-video-downloader/config.yaml
Output directory: /home/user/Downloads/dbdvdl-output
FFmpeg path: ffmpeg
Default language: en
Default download mode: video
Default video quality: best
Default audio quality: best
Retry on network failure: 3
Default exists behavior: skip
Ask for disk usage: false
```

---

## `dbdvdl config remove`

**Description:** Remove the user config directory and its contents.

**Usage:**

```
dbdvdl config remove [OPTIONS]
```

### Options

#### `--yes`, `-y`

| Property | Value |
| --- | --- |
| Type | `bool` |
| Default | `False` |
| Description | Remove config directory without confirmation. Required when running non-interactively (if stdin is not a TTY). |

### Examples

```bash
# Interactive removal (prompts for confirmation)
dbdvdl config remove

# Non-interactive removal
dbdvdl config remove --yes
```

After removal, the command prints a hint showing how to recreate the config:

```
You can create a new config with:
  dbdvdl init
  dbdvdl init --default
  ...
```
