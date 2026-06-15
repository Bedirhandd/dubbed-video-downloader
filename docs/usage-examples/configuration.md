# Configuration Examples

Practical examples for managing the `dbdvdl` configuration system -- creating, inspecting, modifying, and removing config.

## Configuration File Location

The config file lives at:

```
~/.config/dubbed-video-downloader/config.yaml
```

It is created by `dbdvdl init` and read by all other commands. The config file is required -- attempting to use any command without it produces an error.

## Interactive Configuration

Run `dbdvdl init` without options for an interactive setup that prompts for each setting:

```bash
uv run dbdvdl init
```

Example interactive session:

```
Output directory
  Downloads will be saved under this directory.
  Accepted: absolute path, ~ path, or env-var path.
  Default: ~/Downloads/dbdvdl-output (press Enter to use)
Output directory [~/Downloads/dbdvdl-output]: ~/Videos/dubbed

FFmpeg path
  Executable used to merge video and dubbed audio.
  Accepted: `ffmpeg`, `ffmpeg.exe`, or absolute path.
  Default: ffmpeg (press Enter to use)
FFmpeg path [ffmpeg]:

Default language
  Dub language code to use when --lang is omitted.
  Accepted: BCP-47 language code, e.g. en, eng, en-US, tr.
  Default: en (press Enter to use)
Default language [en]: de
...

Wrote config: /home/user/.config/dubbed-video-downloader/config.yaml
```

Pressing Enter at any prompt accepts the default value shown in brackets.

## Quick Setup with All Defaults

Skip all prompts and use built-in defaults:

```bash
uv run dbdvdl init --default
```

This creates a config with:
- `output_dir`: `~/Downloads/dbdvdl-output`
- `ffmpeg_path`: `ffmpeg`
- `default_lang`: `en`
- `default_download_mode`: `video`
- `default_video_quality`: `best`
- `default_audio_quality`: `best`
- `retry_on_network_failure`: `3`
- `default_exists_behavior`: `skip`
- `ask_for_disk_usage`: `false`

## Non-Interactive Setup with Custom Values

Set specific values without prompts by passing options:

```bash
uv run dbdvdl init \
  --output-dir ~/Videos/dubbed \
  --default-lang tr \
  --default-download-mode audio \
  --default-video-quality 1080p \
  --default-audio-quality medium \
  --retry-on-network-failure 5 \
  --default-exists-behavior overwrite
```

Any options you omit are prompted interactively. To skip all prompts while overriding some values, combine with `--default`:

```bash
uv run dbdvdl init --default --default-lang ja --output-dir ~/Videos/dubbed
```

Options specified on the command line take priority over the `--default` preset.

## Viewing the Current Configuration

```bash
uv run dbdvdl config show
```

Expected output:

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

This shows the resolved (loaded and validated) configuration. If the config file is missing or invalid, the command fails with an error.

## Overwriting an Existing Config

By default, `dbdvdl init` refuses to overwrite an existing config:

```bash
uv run dbdvdl init
```

Error output:

```
Config error: Config file already exists at /home/user/.config/dubbed-video-downloader/config.yaml. Use --force to overwrite it.
```

Use `--force` to overwrite:

```bash
# Interactive re-initialization (overwrites existing config)
uv run dbdvdl init --force

# Non-interactive (all defaults, overwrite)
uv run dbdvdl init --default --force

# Change just one setting non-interactively
uv run dbdvdl init --force --default-lang pt-BR
```

When you use `--force` with selective options, any option you don't provide is **prompted interactively** unless you also use `--default`.

## Changing Only One Config Value

Since `dbdvdl init` always prompts for every setting (unless `--default` is used), the simplest way to change one value is:

```bash
# Change only the default language, keep everything else at defaults
uv run dbdvdl init --force --default --default-lang ko
```

## Removing the Configuration

Delete the entire config directory:

```bash
# Interactive (asks for confirmation)
uv run dbdvdl config remove

# Non-interactive (no confirmation prompt)
uv run dbdvdl config remove --yes
```

Expected output:

```
Removed config directory: /home/user/.config/dubbed-video-downloader
```

After removal, the command prints a hint:

```
You can create a new config with:
  dbdvdl init
  dbdvdl init --default
  dbdvdl init --output-dir ~/Videos --ffmpeg-path /path/to/ffmpeg --default-lang tr ...
```

Non-interactive removal without `--yes` is refused:

```bash
echo "" | uv run dbdvdl config remove
```

Error output:

```
Refusing to remove config non-interactively without --yes.
```

## Config File Contents

Here is what a typical config file looks like on disk:

```yaml
output_dir: ~/Downloads/dbdvdl-output
ffmpeg_path: ffmpeg
default_lang: en
default_download_mode: video
default_video_quality: best
default_audio_quality: best
retry_on_network_failure: 3
default_exists_behavior: skip
ask_for_disk_usage: false
```

Keys are always written in this order. Unknown keys are silently ignored during loading, so the config file is forward-compatible.

## Editing the Config File Manually

You can edit `~/.config/dubbed-video-downloader/config.yaml` directly with any text editor:

```bash
# Open in default editor
nano ~/.config/dubbed-video-downloader/config.yaml
```

After editing, verify that the config parses correctly:

```bash
uv run dbdvdl config show
```

If you introduce a syntax error:

```
Config error: Could not parse /home/user/.config/dubbed-video-downloader/config.yaml: ...
```

Validation rules applied on load:
- `output_dir`, `ffmpeg_path`, and `default_lang` are required
- `output_dir` must resolve to an absolute path
- `ffmpeg_path` must be `ffmpeg`, `ffmpeg.exe`, or an absolute path
- `default_lang` must be a valid BCP-47 code (not `und`)
- `retry_on_network_failure` must be a non-negative integer (not a boolean)
- `default_download_mode` must be `video` or `audio`
- `default_video_quality` must be `best`, `medium`, `low`, or a resolution like `1080p`
- `default_audio_quality` must be `best`, `medium`, or `low`
- `default_exists_behavior` must be `skip`, `fail`, or `overwrite`
- `ask_for_disk_usage` must be a boolean (`true` or `false` in YAML)

## CLI Override Behavior

Config values are overridden per-command using CLI flags. The precedence is:

1. **CLI flag** (highest) -- specified directly on the command
2. **Config file** -- loaded from `~/.config/dubbed-video-downloader/config.yaml`
3. **Built-in default** (lowest) -- used when the key is optional and absent from config

Example: the config has `default_lang: en`, but you want Japanese for one download:

```bash
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang ja
```

The config file is never modified by CLI overrides. The change is in effect only for that single command.

## Handling Disk Usage Confirmation

When `ask_for_disk_usage` is `true` in config, each download prompts:

```bash
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID"
```

Expected prompt:

```
This download is estimated to use ~250 MB of disk space. Continue? [y/N]:
```

- `y` or `Enter` → proceed with download
- `n` → cancel this URL (continues to next URL in multi-URL downloads)
- `--yes` / `-y` → approve without being prompted

To disable disk usage prompts permanently, re-initialize config:

```bash
uv run dbdvdl init --force --no-ask-for-disk-usage
```

## Example: Config for a Bandwidth-Conscious Setup

```bash
uv run dbdvdl init --default \
  --default-video-quality 720p \
  --default-audio-quality medium \
  --default-download-mode video
```

## Example: Config for Audio-Only Extraction

```bash
uv run dbdvdl init --default \
  --default-download-mode audio \
  --default-audio-quality best \
  --output-dir ~/Music/dubbed-audio
```

## Example: Config for Scripting and Automation

```bash
uv run dbdvdl init --default \
  --retry-on-network-failure 5 \
  --default-exists-behavior skip \
  --no-ask-for-disk-usage
```

The `--no-ask-for-disk-usage` ensures downloads run without interactive prompts, which is essential for cron jobs and scripts.

## Verification After Config Changes

Always verify your config after making changes:

```bash
uv run dbdvdl config show
uv run dbdvdl doctor
```

`doctor` also checks that the output directory is writable and FFmpeg/Node.js are accessible.

## Next Steps

- [Basic Downloads](basic-downloads.md) -- Using the configured settings for downloads
- [Language and Dubs](language-and-dubs.md) -- Language code formats and resolution
- [Batch and Multiple URLs](batch-and-playlists.md) -- Downloading multiple videos
